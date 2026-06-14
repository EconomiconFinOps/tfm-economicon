from fastapi import Request


def get_database(request: Request):
    return request.app.state.database


def get_queue(request: Request):
    return request.app.state.queue


def get_vector_store(request: Request):
    return request.app.state.vector_store
