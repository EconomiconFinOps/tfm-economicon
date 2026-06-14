from sqlalchemy import text


def upgrade(connection) -> None:
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id STRING PRIMARY KEY,
                name STRING NOT NULL,
                slug STRING UNIQUE NOT NULL,
                plan STRING NOT NULL
            )
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS users (
                id STRING PRIMARY KEY,
                email STRING UNIQUE NOT NULL,
                password_hash STRING NOT NULL,
                full_name STRING NOT NULL,
                role STRING NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS user_tenants (
                user_id STRING NOT NULL,
                tenant_id STRING NOT NULL,
                role STRING NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (user_id, tenant_id)
            )
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id STRING PRIMARY KEY,
                tenant_id STRING NOT NULL,
                created_by STRING NOT NULL,
                source STRING NOT NULL,
                artifact_uri STRING,
                payload JSONB NOT NULL,
                status STRING NOT NULL,
                result JSONB,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id STRING PRIMARY KEY,
                tenant_id STRING NOT NULL,
                user_id STRING NOT NULL,
                title STRING NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id STRING PRIMARY KEY,
                conversation_id STRING NOT NULL,
                tenant_id STRING NOT NULL,
                user_id STRING,
                role STRING NOT NULL,
                content STRING NOT NULL,
                metadata JSONB,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    )
