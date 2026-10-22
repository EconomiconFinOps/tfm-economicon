from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.aws_bootstrap_common import BootstrapError


SUB = 'dd0a7871-d3c3-441f-9c40-d01aee724131'
EMAIL = 'aws-defensa+ensayo1@example.com'
MARKER = 'JUP-131:ensayo1:' + 'a' * 40


class MissingUser(Exception):
    response = {'Error': {'Code': 'UserNotFoundException'}}


def setup_context():
    client = Mock()
    attributes = [{'Name': key, 'Value': value} for key, value in {
        'sub': SUB, 'email': EMAIL, 'email_verified': 'true', 'custom:rehearsal': MARKER,
    }.items()]
    client.admin_get_user.side_effect = MissingUser()
    client.admin_create_user.return_value = {'User': {'Username': SUB, 'Attributes': attributes}}
    context = SimpleNamespace(
        inputs={'cycle_id': 'ensayo1', 'source_sha': 'a' * 40, 'rehearsal_secret_arn': 'bundle',
                'cognito': {'user_pool_id': 'eu-south-2_Synthetic131'}},
        client=Mock(return_value=client),
        secret=Mock(return_value={'_cycle_id': 'ensayo1', '_source_sha': 'a' * 40,
                                  'smoke_user': {'email': EMAIL, 'password': 'Ec1!' + 'b' * 48}}))
    return context, client, attributes


def test_private_user_creation_suppresses_email_and_uses_authoritative_sub():
    from app.aws_bootstrap_identity import ensure_identity
    context, client, attributes = setup_context()
    assert ensure_identity(context) == {'id': SUB, 'email': EMAIL}
    request = client.admin_create_user.call_args.kwargs
    assert request['MessageAction'] == 'SUPPRESS'
    assert request['Username'] == EMAIL
    assert {a['Name']: a['Value'] for a in request['UserAttributes']}['custom:rehearsal'] == MARKER
    assert client.admin_set_user_password.call_args.kwargs == {
        'UserPoolId': 'eu-south-2_Synthetic131', 'Username': SUB,
        'Password': 'Ec1!' + 'b' * 48, 'Permanent': True}
    client.admin_get_user.side_effect = None
    client.admin_get_user.return_value = {'Username': SUB, 'UserAttributes': attributes}
    ensure_identity(context)
    assert client.admin_create_user.call_count == 1


@pytest.mark.parametrize('field,value', [('custom:rehearsal', 'foreign'), ('sub', 'not-a-sub'),
                                         ('email', 'foreign@example.com'), ('email_verified', 'false')])
def test_existing_foreign_identity_is_never_reset(field, value):
    from app.aws_bootstrap_identity import ensure_identity
    context, client, attributes = setup_context()
    for attr in attributes:
        if attr['Name'] == field:
            attr['Value'] = value
    client.admin_get_user.side_effect = None
    client.admin_get_user.return_value = {'Username': SUB, 'UserAttributes': attributes}
    with pytest.raises(BootstrapError):
        ensure_identity(context)
    client.admin_set_user_password.assert_not_called()
    client.admin_create_user.assert_not_called()


def test_service_failure_does_not_leak_response_or_credentials():
    from app.aws_bootstrap_identity import ensure_identity
    context, client, _ = setup_context()
    client.admin_get_user.side_effect = RuntimeError('synthetic-private-credentials')
    with pytest.raises(BootstrapError) as caught:
        ensure_identity(context)
    assert 'synthetic-private' not in str(caught.value)
    client.admin_set_user_password.assert_not_called()


@pytest.fixture
def identity_database():
    import importlib
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://')
    with engine.begin() as connection:
        importlib.import_module('app.db.migrations.001_initial').upgrade(connection)
    yield engine
    engine.dispose()


def test_membership_is_restartable_and_only_authorizes_core(identity_database):
    from sqlalchemy import text
    from app.aws_bootstrap_identity import bind_identity
    identity = {'id': SUB, 'email': EMAIL}
    bind_identity(identity_database, identity)
    bind_identity(identity_database, identity)
    with identity_database.connect() as connection:
        assert connection.execute(text('SELECT id,email,password_hash,role FROM users')).one() == (
            SUB, EMAIL, '!cognito-only', 'analyst')
        assert connection.execute(text('SELECT user_id,tenant_id,role FROM user_tenants')).all() == [
            (SUB, 'tenant-core', 'analyst')]
        assert connection.execute(text('SELECT count(*) FROM tenants')).scalar_one() == 2


@pytest.mark.parametrize('collision', ['email', 'subject', 'membership', 'tenant'])
def test_conflicting_local_state_rolls_back_without_linking(identity_database, collision):
    from sqlalchemy import text
    from app.aws_bootstrap_identity import bind_identity
    identity = {'id': SUB, 'email': EMAIL}
    bind_identity(identity_database, identity)
    with identity_database.begin() as connection:
        if collision == 'email':
            connection.execute(text("UPDATE users SET id='different-sub'"))
        elif collision == 'subject':
            connection.execute(text("UPDATE users SET email='foreign@example.com'"))
        elif collision == 'membership':
            connection.execute(text("INSERT INTO user_tenants SELECT user_id,'tenant-growth',role,created_at FROM user_tenants"))
        else:
            connection.execute(text("UPDATE tenants SET slug='foreign' WHERE id='tenant-core'"))
    with pytest.raises(BootstrapError):
        bind_identity(identity_database, identity)
    with identity_database.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM users')).scalar_one() == 1
