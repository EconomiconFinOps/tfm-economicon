"""Keep cached vectors unchanged while admitting explicit native model spaces.

Legacy chunk_embeddings retains its original dimensionality. Only the verified
cache can contain several dimensions, each bound to an immutable space_id and
checked against that space before insertion and query.
"""
from sqlalchemy import text


def upgrade(connection):
    connection.execute(text('ALTER TABLE embedding_cache ALTER COLUMN embedding TYPE vector'))
    connection.execute(text('ALTER TABLE embedding_cache ADD CONSTRAINT embedding_cache_native_dimensions '
                            'CHECK (vector_dims(embedding) IN (256,512,1024,1536))'))
