"""Admin-created rehearsal identity, bound by Cognito sub and immutable marker."""
import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import text

from app.aws_bootstrap_common import BootstrapError, require


def _error_code(error):
    return getattr(error, 'response', {}).get('Error', {}).get('Code')


def ensure_identity(context):
    try:
        inputs = context.inputs
        cycle, source = inputs['cycle_id'], inputs['source_sha']
        require(re.fullmatch(r'(?:ensayo[0-9][a-z0-9]{0,3}|defensa[0-9]{0,2})', cycle)
                and re.fullmatch(r'[a-f0-9]{40}', source))
        pool = inputs['cognito']['user_pool_id']
        require(re.fullmatch(r'eu-west-1_[A-Za-z0-9]+', pool))
        bundle = context.secret(inputs['rehearsal_secret_arn'])
        require(bundle['_cycle_id'] == cycle and bundle['_source_sha'] == source)
        email = 'aws-defensa+' + cycle + '@example.com'
        password = bundle['smoke_user']['password']
        require(bundle['smoke_user']['email'] == email and isinstance(password, str)
                and re.fullmatch(r'Ec1![a-f0-9]{48}', password))
        marker = 'JUP-131:' + cycle + ':' + source
        client = context.client('cognito-idp', 'eu-west-1')
        try:
            existing = client.admin_get_user(UserPoolId=pool, Username=email)
        except Exception as error:
            if _error_code(error) != 'UserNotFoundException':
                raise
            try:
                created = client.admin_create_user(
                    UserPoolId=pool, Username=email, MessageAction='SUPPRESS',
                    TemporaryPassword=password, UserAttributes=[
                        {'Name': 'email', 'Value': email}, {'Name': 'email_verified', 'Value': 'true'},
                        {'Name': 'custom:rehearsal', 'Value': marker}])['User']
                existing = {'Username': created['Username'], 'UserAttributes': created['Attributes']}
            except Exception as create_error:
                if _error_code(create_error) != 'UsernameExistsException':
                    raise
                existing = client.admin_get_user(UserPoolId=pool, Username=email)
        attributes = existing['UserAttributes']
        require(len({attr['Name'] for attr in attributes}) == len(attributes))
        values = {attr['Name']: attr['Value'] for attr in attributes}
        sub = values['sub']
        require(str(UUID(sub)) == sub and existing['Username'] == sub
                and values.get('email') == email and values.get('email_verified') == 'true'
                and values.get('custom:rehearsal') == marker)
        client.admin_set_user_password(UserPoolId=pool, Username=sub, Password=password, Permanent=True)
        return {'id': sub, 'email': email}
    except Exception:
        raise BootstrapError('Rehearsal identity is unavailable or has conflicting ownership.') from None


def bind_identity(engine, identity):
    """Never join an existing local account by email or extend its memberships."""
    from app.db.database import TENANT_SEED
    require(str(UUID(identity['id'])) == identity['id'] and re.fullmatch(
        r'aws-defensa\+(?:ensayo[0-9][a-z0-9]{0,3}|defensa[0-9]{0,2})@example\.com', identity['email']))
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        for tenant in TENANT_SEED:
            rows = connection.execute(text('SELECT id,name,slug,plan FROM tenants WHERE id=:id OR slug=:slug'), tenant).mappings().all()
            require(not rows or len(rows) == 1 and dict(rows[0]) == tenant)
            connection.execute(text('INSERT INTO tenants(id,name,slug,plan) VALUES(:id,:name,:slug,:plan) ON CONFLICT DO NOTHING'), tenant)
        expected = dict(identity, password_hash='!cognito-only', full_name='AWS rehearsal operator', role='analyst')
        rows = connection.execute(text('SELECT id,email,password_hash,full_name,role FROM users WHERE id=:id OR email=:email'), identity).mappings().all()
        require(not rows or len(rows) == 1 and dict(rows[0]) == expected)
        memberships = connection.execute(text('SELECT tenant_id,role FROM user_tenants WHERE user_id=:id'), identity).all()
        require(not memberships or memberships == [('tenant-core', 'analyst')])
        connection.execute(text('''INSERT INTO users(id,email,password_hash,full_name,role,created_at)
            VALUES(:id,:email,:password_hash,:full_name,:role,:created_at) ON CONFLICT DO NOTHING'''), dict(expected, created_at=now))
        connection.execute(text('''INSERT INTO user_tenants(user_id,tenant_id,role,created_at)
            VALUES(:id,'tenant-core','analyst',:created_at) ON CONFLICT DO NOTHING'''), dict(identity, created_at=now))
