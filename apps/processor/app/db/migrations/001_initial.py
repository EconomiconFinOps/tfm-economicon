def upgrade(connection) -> None:
    # jobs belongs to the backend; creating it here too races on concurrent cold starts.
    pass
