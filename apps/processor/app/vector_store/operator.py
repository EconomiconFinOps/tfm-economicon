"""Existing tenant/document authority for a service operator; no new user role."""
from sqlalchemy import bindparam, text


def catalog_authorizer(database, store, tenant, operator):
    if not tenant or not operator:
        raise ValueError('Existing operator and tenant are required')
    def authorize():
        with database.engine.connect() as connection:
            membership = connection.execute(text('''SELECT u.id FROM users u JOIN user_tenants ut ON ut.user_id=u.id
                WHERE u.id=:operator AND ut.tenant_id=:tenant'''), {'operator': operator, 'tenant': tenant}).first()
            if membership is None:
                raise PermissionError('Index operator is not a current tenant member')
            with store.engine.connect() as vector_connection:
                ids = set(vector_connection.execute(text('SELECT id FROM knowledge_documents WHERE tenant_id=:tenant'), {'tenant': tenant}).scalars())
            if not ids: return
            admitted = set(connection.execute(text('''SELECT j.id FROM jobs j JOIN users u ON u.id=j.created_by
                JOIN user_tenants ut ON ut.user_id=u.id AND ut.tenant_id=j.tenant_id
                WHERE j.tenant_id=:tenant AND j.status='completed' AND j.id IN :ids''')
                .bindparams(bindparam('ids', expanding=True)), {'tenant': tenant, 'ids': sorted(ids)}).scalars())
            if admitted != ids:
                raise PermissionError('Catalog includes documents without current completed-job authority')
    return authorize
