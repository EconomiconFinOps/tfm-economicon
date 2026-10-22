"""Verified immutable index snapshots and tenant-scoped embedding reuse."""
import json
import math
import uuid
import hashlib
from sqlalchemy import bindparam, text
from app.embeddings.context import prepare_embedding
from app.embeddings.space import EmbeddingSpace, canonical, digest


class StaleGeneration(RuntimeError):
    pass


def lock_head(connection, tenant):
    connection.execute(text('INSERT INTO tenant_rag_head(tenant_id) VALUES(:tenant) ON CONFLICT DO NOTHING'), {'tenant': tenant})
    return connection.execute(text('SELECT * FROM tenant_rag_head WHERE tenant_id=:tenant FOR UPDATE'), {'tenant': tenant}).mappings().one()


def snapshot_document(connection, document, chunks):
    tenant = document['tenant_id']
    revision = digest({'document': document, 'chunks': chunks})
    connection.execute(text('''INSERT INTO rag_document_revisions
        (tenant_id,id,document_id,publication_id,source,content,metadata)
        VALUES(:tenant,:id,:document,:publication,:source,:content,CAST(:metadata AS jsonb)) ON CONFLICT DO NOTHING'''),
        {'tenant': tenant, 'id': revision, 'document': document['id'], 'publication': document['publication_id'],
         'source': document['source'], 'content': document['content'], 'metadata': canonical(document['metadata'])})
    for chunk in chunks:
        connection.execute(text('''INSERT INTO rag_revision_chunks(tenant_id,revision_id,chunk_id,chunk_index,content,metadata)
            VALUES(:tenant,:revision,:id,:position,:content,CAST(:metadata AS jsonb)) ON CONFLICT DO NOTHING'''),
            {'tenant': tenant, 'revision': revision, 'id': chunk['chunk_id'], 'position': chunk['chunk_index'],
             'content': chunk['content'], 'metadata': canonical(chunk['metadata'])})
    return revision


class GenerationStore:
    def __init__(self, engine, counter=None):
        self.engine, self.counter = engine, counter

    def register_space(self, space):
        with self.engine.begin() as connection:
            connection.execute(text('INSERT INTO embedding_spaces(id,descriptor) VALUES(:id,CAST(:data AS jsonb)) ON CONFLICT DO NOTHING'),
                               {'id': space.id, 'data': canonical(space.descriptor())})
            actual = connection.execute(text('SELECT descriptor FROM embedding_spaces WHERE id=:id'), {'id': space.id}).scalar_one()
            if actual != space.descriptor():
                raise ValueError('Embedding space fingerprint collision')

    def active_plan(self, tenant):
        with self.engine.connect() as connection:
            return self._read_plan(connection, tenant)

    @staticmethod
    def _read_plan(connection, tenant):
        row = connection.execute(text('''SELECT h.generation_id,h.version,h.catalog_revision,g.space_id,s.descriptor
                FROM tenant_rag_head h LEFT JOIN rag_generations g ON g.tenant_id=h.tenant_id AND g.id=h.generation_id
                LEFT JOIN embedding_spaces s ON s.id=g.space_id WHERE h.tenant_id=:tenant'''), {'tenant': tenant}).mappings().first()
        return dict(row) if row else {'generation_id': None, 'version': 0, 'catalog_revision': 0}

    def cache_embeddings(self, tenant, space, prepared, provider):
        self.register_space(space)
        if (provider.name != space.provider or provider.dimension != space.dimension
                or (provider.name in {'litellm','bedrock'} and getattr(provider, 'mapping_sha256', None) != space.mapping_sha256)):
            raise ValueError('Provider is incompatible with the requested embedding space')
        unique = {item.text_hash: item for item in prepared}
        if any(not isinstance(item.text, str) or not item.text.strip()
               or hashlib.sha256(item.text.encode('utf-8')).hexdigest() != item.text_hash
               or type(item.token_count) is not int or not 0 < item.token_count <= space.max_input_tokens
               or (self.counter is not None and self.counter.count(item.text) != item.token_count) for item in prepared):
            raise ValueError('Embedding text/hash/token identity mismatch')
        if not unique:
            return {}
        query = text('''SELECT text_hash,embedding::text AS vector FROM embedding_cache
            WHERE tenant_id=:tenant AND space_id=:space AND text_hash IN :hashes''').bindparams(bindparam('hashes', expanding=True))
        parameters = {'tenant': tenant, 'space': space.id, 'hashes': list(unique)}
        with self.engine.connect() as connection:
            known = {row.text_hash: json.loads(row.vector) for row in connection.execute(query, parameters)}
        missing = [item for key, item in unique.items() if key not in known]
        if missing:
            vectors = provider.embed_batch([item.text for item in missing], expected_model=space.model_id, counter=self.counter)
            if len(vectors) != len(missing):
                raise ValueError('Incomplete embedding result')
            for item, vector in zip(missing, vectors):
                if (len(vector) != space.dimension or any(type(v) not in {int, float} or not math.isfinite(v) for v in vector)
                        or not any(float(f'{v:.6f}') != 0 for v in vector)):
                    raise ValueError('Invalid cache vector')
            with self.engine.begin() as connection:
                for item, vector in zip(missing, vectors):
                    connection.execute(text('''INSERT INTO embedding_cache(tenant_id,space_id,text_hash,embedding,token_count)
                        VALUES(:tenant,:space,:hash,CAST(:vector AS vector),:tokens) ON CONFLICT DO NOTHING'''),
                        {'tenant': tenant, 'space': space.id, 'hash': item.text_hash,
                         'vector': '[' + ','.join(f'{v:.6f}' for v in vector) + ']', 'tokens': item.token_count})
                # A concurrent winner is canonical: never publish a losing HTTP result.
                known = {row.text_hash: json.loads(row.vector) for row in connection.execute(query, parameters)}
        if set(known) != set(unique) or any(len(v) != space.dimension or not any(v) or not all(math.isfinite(x) for x in v) for v in known.values()):
            raise ValueError('Invalid or incomplete embedding cache')
        with self.engine.begin() as connection:
            connection.execute(text('UPDATE embedding_cache SET last_used_at=clock_timestamp() WHERE tenant_id=:tenant AND space_id=:space AND text_hash IN :hashes')
                .bindparams(bindparam('hashes', expanding=True)), parameters)
        return known

    def build(self, tenant, space, provider, *, retrieval_mode='dense', rrf_k=60, authorize=None):
        if retrieval_mode not in {'dense', 'hybrid'} or type(rrf_k) is not int or not 1 <= rrf_k <= 1000:
            raise ValueError('Invalid retrieval mode')
        if authorize is not None:
            authorize()
        self.register_space(space)
        identifier = str(uuid.uuid4())
        execution = str(uuid.uuid4())
        captured = []
        with self.engine.begin() as connection:
            head = lock_head(connection, tenant)
            if authorize is not None:
                authorize()
            documents = connection.execute(text('SELECT id,source,text_content,metadata FROM knowledge_documents WHERE tenant_id=:tenant ORDER BY id'), {'tenant': tenant}).mappings().all()
            connection.execute(text('''INSERT INTO rag_generations(tenant_id,id,space_id,state,catalog_revision,retrieval_config,manifest)
                VALUES(:tenant,:id,:space,'building',:revision,CAST(:config AS jsonb),CAST(:manifest AS jsonb))'''),
                {'tenant': tenant, 'id': identifier, 'space': space.id, 'revision': head['catalog_revision'],
                 'manifest': canonical({'build_execution_id': execution}),
                 'config': canonical({'mode': retrieval_mode, 'rrf_k': rrf_k, 'candidate_limit': 20, 'lexical_policy': 'literal_context_v1'})})
            for row in documents:
                chunks = [dict(item) for item in connection.execute(text('''SELECT id AS chunk_id,chunk_index,content,metadata FROM document_chunks
                    WHERE document_id=:document ORDER BY chunk_index'''), {'document': row['id']}).mappings()]
                document = {'tenant_id': tenant, 'id': row['id'], 'source': row['source'], 'content': row['text_content'],
                            'metadata': row['metadata'], 'publication_id': row['metadata'].get('publication_id', 'legacy')}
                revision = snapshot_document(connection, document, chunks)
                connection.execute(text('INSERT INTO rag_generation_members(tenant_id,generation_id,document_id,revision_id) VALUES(:tenant,:generation,:document,:revision)'),
                                   {'tenant': tenant, 'generation': identifier, 'document': row['id'], 'revision': revision})
                captured.append((revision, document, chunks))
        return self._finish_build(tenant, identifier, space, provider, captured, authorize, execution)

    def resume(self, tenant, identifier, provider, *, authorize=None):
        if authorize is not None: authorize()
        execution = str(uuid.uuid4())
        captured = []
        with self.engine.begin() as connection:
            head = lock_head(connection, tenant)
            row = connection.execute(text('''SELECT g.*,s.descriptor FROM rag_generations g JOIN embedding_spaces s ON s.id=g.space_id
                WHERE g.tenant_id=:tenant AND g.id=:id FOR UPDATE OF g'''), {'tenant': tenant, 'id': identifier}).mappings().first()
            if not row or row['state'] not in {'building', 'failed'} or row['catalog_revision'] != head['catalog_revision']:
                raise StaleGeneration('Only an unfinished generation of the current catalog can resume')
            space = EmbeddingSpace.from_descriptor(row['descriptor'])
            documents = connection.execute(text('''SELECT r.* FROM rag_generation_members m JOIN rag_document_revisions r
                ON r.tenant_id=m.tenant_id AND r.id=m.revision_id WHERE m.tenant_id=:tenant AND m.generation_id=:id ORDER BY m.document_id'''),
                {'tenant': tenant, 'id': identifier}).mappings().all()
            for document in documents:
                chunks = [dict(item) for item in connection.execute(text('SELECT chunk_id,chunk_index,content,metadata FROM rag_revision_chunks WHERE tenant_id=:tenant AND revision_id=:revision ORDER BY chunk_index'),
                    {'tenant': tenant, 'revision': document['id']}).mappings()]
                captured.append((document['id'], {**dict(document), 'id': document['document_id']}, chunks))
            connection.execute(text("UPDATE rag_generations SET state='building',retired_at=NULL,manifest=CAST(:manifest AS jsonb) WHERE tenant_id=:tenant AND id=:id"),
                               {'tenant': tenant, 'id': identifier, 'manifest': canonical({'build_execution_id': execution})})
        return self._finish_build(tenant, identifier, space, provider, captured, authorize, execution)

    def _finish_build(self, tenant, identifier, space, provider, captured, authorize, execution):
        try:
            warnings = []
            for revision, document, chunks in captured:
                diagnostics = self._vectorize_revision(tenant, revision, document['metadata'], chunks, space, provider)
                warnings.extend({'document_id': document['id'], 'revision_id': revision, **item} for item in diagnostics)
            manifest = {'documents': [{'id': doc['id'], 'revision': revision, 'publication_id': doc['publication_id'],
                                       'chunks': len(chunks)} for revision, doc, chunks in captured],
                        'chunk_count': sum(len(chunks) for _, _, chunks in captured),
                        'preparation_warnings': warnings}
            manifest['fingerprint'] = digest(manifest)
            with self.engine.begin() as connection:
                if authorize is not None:
                    authorize()
                # Serialize only the final transition, never the remote work.
                owner = connection.execute(text("SELECT state,manifest->>'build_execution_id' AS execution FROM rag_generations WHERE tenant_id=:tenant AND id=:id FOR UPDATE"),
                                           {'tenant': tenant, 'id': identifier}).mappings().one()
                if owner['state'] != 'building' or owner['execution'] != execution:
                    raise StaleGeneration('Build execution was superseded')
                self._check_complete(connection, tenant, identifier, space.id, manifest['chunk_count'])
                updated = connection.execute(text("UPDATE rag_generations SET state='ready',manifest=CAST(:manifest AS jsonb) WHERE tenant_id=:tenant AND id=:id AND state='building' AND manifest->>'build_execution_id'=:execution"),
                                   {'tenant': tenant, 'id': identifier, 'manifest': canonical(manifest), 'execution': execution})
                if updated.rowcount != 1:
                    raise StaleGeneration('Build execution was superseded')
        except Exception:
            with self.engine.begin() as connection:
                connection.execute(text("UPDATE rag_generations SET state='failed',retired_at=clock_timestamp() WHERE tenant_id=:tenant AND id=:id AND state='building' AND manifest->>'build_execution_id'=:execution"),
                                   {'tenant': tenant, 'id': identifier, 'execution': execution})
            raise
        return identifier

    def _vectorize_revision(self, tenant, revision, metadata, chunks, space, provider):
        prepared = [prepare_embedding(chunk, metadata, space, self.counter) for chunk in chunks]
        self.cache_embeddings(tenant, space, prepared, provider)
        with self.engine.begin() as connection:
            for chunk, item in zip(chunks, prepared):
                connection.execute(text('''INSERT INTO rag_chunk_vectors(tenant_id,revision_id,chunk_id,space_id,text_hash)
                    VALUES(:tenant,:revision,:chunk,:space,:hash) ON CONFLICT DO NOTHING'''),
                    {'tenant': tenant, 'revision': revision, 'chunk': chunk['chunk_id'], 'space': space.id, 'hash': item.text_hash})
        # Diagnostics belong to the source revision/preparation, not a shared
        # text-hash cache entry: a shortened and an exact title can embed alike.
        return [{'chunk_id': chunk['chunk_id'], 'warnings': list(item.warnings)}
                for chunk, item in zip(chunks, prepared) if item.warnings]

    def prepare_publication(self, tenant, document_id, source, content, chunks, metadata, provider):
        """Perform remote work before the short catalog/publication transaction."""
        plan = self.active_plan(tenant)
        if plan['generation_id'] is None:
            return None
        space = EmbeddingSpace.from_descriptor(plan['descriptor'])
        items = publication_chunks(document_id, chunks)
        prepared = [prepare_embedding(item, metadata or {}, space, self.counter) for item in items]
        vectors = self.cache_embeddings(tenant, space, prepared, provider)
        return {'generation_id': plan['generation_id'], 'version': plan['version'], 'space_id': space.id,
                'payload_hash': digest({'id': document_id, 'source': source, 'content': content,
                                        'chunks': items, 'metadata': metadata or {}}),
                'text_hashes': [item.text_hash for item in prepared],
                'preparation_warnings': [list(item.warnings) for item in prepared],
                'plain_embeddings': [vectors[item.text_hash] for item in prepared] if space.preparation == 'plain_v1' else None}

    def publish_prepared(self, connection, tenant, head, document, chunks, prepared):
        """Clone membership and switch the whole index in the catalog transaction."""
        if (not prepared or prepared['generation_id'] != head['generation_id']
                or prepared['version'] != head['version']):
            raise StaleGeneration('The active index changed during publication preparation')
        metadata = {key: value for key, value in document['metadata'].items() if key != 'publication_id'}
        expected = digest({'id': document['id'], 'source': document['source'], 'content': document['content'],
                           'chunks': chunks, 'metadata': metadata})
        warnings = prepared.get('preparation_warnings')
        if (expected != prepared['payload_hash'] or len(prepared['text_hashes']) != len(chunks)
                or not isinstance(warnings, list) or len(warnings) != len(chunks)
                or any(not isinstance(item, list) or any(code != 'embedding_context_truncated' for code in item)
                       for item in warnings)):
            raise ValueError('Prepared index does not match the document publication')
        old = connection.execute(text('SELECT * FROM rag_generations WHERE tenant_id=:tenant AND id=:id'),
                                 {'tenant': tenant, 'id': head['generation_id']}).mappings().one()
        if old['space_id'] != prepared['space_id']:
            raise StaleGeneration('The embedding space changed')
        self._check_manifest(connection, tenant, old['id'], old['manifest'])
        revision = snapshot_document(connection, document, chunks)
        for chunk, text_hash in zip(chunks, prepared['text_hashes']):
            connection.execute(text('''INSERT INTO rag_chunk_vectors(tenant_id,revision_id,chunk_id,space_id,text_hash)
                VALUES(:tenant,:revision,:chunk,:space,:hash) ON CONFLICT DO NOTHING'''),
                {'tenant': tenant, 'revision': revision, 'chunk': chunk['chunk_id'], 'space': old['space_id'], 'hash': text_hash})
        identifier = str(uuid.uuid4())
        connection.execute(text('''INSERT INTO rag_generations(tenant_id,id,space_id,state,catalog_revision,retrieval_config)
            VALUES(:tenant,:id,:space,'building',:catalog,CAST(:config AS jsonb))'''),
            {'tenant': tenant, 'id': identifier, 'space': old['space_id'], 'catalog': head['catalog_revision'] + 1,
             'config': canonical(old['retrieval_config'])})
        connection.execute(text('''INSERT INTO rag_generation_members(tenant_id,generation_id,document_id,revision_id)
            SELECT tenant_id,:new,document_id,revision_id FROM rag_generation_members
            WHERE tenant_id=:tenant AND generation_id=:old AND document_id<>:document'''),
            {'tenant': tenant, 'new': identifier, 'old': old['id'], 'document': document['id']})
        connection.execute(text('INSERT INTO rag_generation_members VALUES(:tenant,:generation,:document,:revision)'),
                           {'tenant': tenant, 'generation': identifier, 'document': document['id'], 'revision': revision})
        rows = connection.execute(text('''SELECT m.document_id AS id,m.revision_id AS revision,r.publication_id,count(c.chunk_id) AS chunks
            FROM rag_generation_members m JOIN rag_document_revisions r ON r.tenant_id=m.tenant_id AND r.id=m.revision_id
            LEFT JOIN rag_revision_chunks c ON c.tenant_id=m.tenant_id AND c.revision_id=m.revision_id
            WHERE m.tenant_id=:tenant AND m.generation_id=:id
            GROUP BY m.document_id,m.revision_id,r.publication_id ORDER BY m.document_id'''),
            {'tenant': tenant, 'id': identifier}).mappings().all()
        diagnostics = [item for item in old['manifest'].get('preparation_warnings', [])
                       if item['document_id'] != document['id']]
        diagnostics.extend({'document_id': document['id'], 'revision_id': revision,
                            'chunk_id': chunk['chunk_id'], 'warnings': codes}
                           for chunk, codes in zip(chunks, warnings) if codes)
        diagnostics.sort(key=lambda item: (item['document_id'], item['chunk_id']))
        manifest = {'documents': [dict(row) for row in rows], 'chunk_count': sum(row['chunks'] for row in rows),
                    'preparation_warnings': diagnostics}
        manifest['fingerprint'] = digest(manifest)
        self._check_complete(connection, tenant, identifier, old['space_id'], manifest['chunk_count'])
        connection.execute(text("UPDATE rag_generations SET state='ready',manifest=CAST(:manifest AS jsonb) WHERE tenant_id=:tenant AND id=:id"),
                           {'tenant': tenant, 'id': identifier, 'manifest': canonical(manifest)})
        connection.execute(text("UPDATE rag_generations SET state='retired',retired_at=clock_timestamp() WHERE tenant_id=:tenant AND id=:id"),
                           {'tenant': tenant, 'id': old['id']})
        connection.execute(text('''UPDATE tenant_rag_head SET previous_generation_id=generation_id,generation_id=:id,version=version+1
            WHERE tenant_id=:tenant'''), {'tenant': tenant, 'id': identifier})
        return identifier

    @staticmethod
    def _check_complete(connection, tenant, generation, space, expected):
        parameters = {'tenant': tenant, 'generation': generation, 'space': space}
        counts = connection.execute(text('''SELECT count(*) AS chunks,count(v.chunk_id) AS vectors
            FROM rag_generation_members m JOIN rag_revision_chunks c ON c.tenant_id=m.tenant_id AND c.revision_id=m.revision_id
            LEFT JOIN rag_chunk_vectors v ON v.tenant_id=c.tenant_id AND v.revision_id=c.revision_id AND v.chunk_id=c.chunk_id AND v.space_id=:space
            WHERE m.tenant_id=:tenant AND m.generation_id=:generation'''), parameters).one()
        if counts.chunks != expected or counts.vectors != expected:
            raise ValueError('Incomplete index generation')

    def activate(self, tenant, generation, *, expected_head, expected_version, authorize=None, _rollback=False):
        if authorize is not None:
            authorize()
        with self.engine.begin() as connection:
            head = lock_head(connection, tenant)
            if head['generation_id'] != expected_head or head['version'] != expected_version:
                raise StaleGeneration('The active index changed')
            if generation == head['generation_id']:
                return self._read_plan(connection, tenant)
            candidate = connection.execute(text('SELECT * FROM rag_generations WHERE tenant_id=:tenant AND id=:id FOR UPDATE'),
                                           {'tenant': tenant, 'id': generation}).mappings().first()
            rollback_ready = candidate and _rollback and head['previous_generation_id'] == generation and candidate['state'] == 'retired'
            if not candidate or (candidate['state'] != 'ready' and not rollback_ready):
                raise ValueError('Only a complete ready generation can be activated')
            if candidate['catalog_revision'] != head['catalog_revision']:
                raise StaleGeneration('The source catalog changed during index preparation')
            self._check_complete(connection, tenant, generation, candidate['space_id'], candidate['manifest']['chunk_count'])
            self._check_manifest(connection, tenant, generation, candidate['manifest'])
            if authorize is not None:
                authorize()
            connection.execute(text("UPDATE rag_generations SET state='ready',retired_at=NULL WHERE tenant_id=:tenant AND id=:id"),
                               {'tenant': tenant, 'id': generation})
            connection.execute(text('''UPDATE tenant_rag_head SET generation_id=:id,previous_generation_id=generation_id,version=version+1
                WHERE tenant_id=:tenant'''), {'tenant': tenant, 'id': generation})
            if head['generation_id'] and head['generation_id'] != generation:
                connection.execute(text("UPDATE rag_generations SET state='retired',retired_at=clock_timestamp() WHERE tenant_id=:tenant AND id=:id"),
                                   {'tenant': tenant, 'id': head['generation_id']})
            result = self._read_plan(connection, tenant)
        return result

    @staticmethod
    def _check_manifest(connection, tenant, generation, manifest):
        unsigned = {key: value for key, value in manifest.items() if key != 'fingerprint'}
        if digest(unsigned) != manifest.get('fingerprint'):
            raise ValueError('Invalid generation manifest fingerprint')
        rows = connection.execute(text('''SELECT m.document_id AS id,m.revision_id AS revision,r.publication_id,count(c.chunk_id) AS chunks
            FROM rag_generation_members m JOIN rag_document_revisions r ON r.tenant_id=m.tenant_id AND r.id=m.revision_id
            LEFT JOIN rag_revision_chunks c ON c.tenant_id=m.tenant_id AND c.revision_id=m.revision_id
            WHERE m.tenant_id=:tenant AND m.generation_id=:id
            GROUP BY m.document_id,m.revision_id,r.publication_id ORDER BY m.document_id'''), {'tenant': tenant, 'id': generation}).mappings().all()
        if [dict(row) for row in rows] != manifest.get('documents'):
            raise ValueError('Incomplete generation membership manifest')

    def rollback(self, tenant, *, expected_head, expected_version, authorize=None):
        with self.engine.connect() as connection:
            head = connection.execute(text('SELECT * FROM tenant_rag_head WHERE tenant_id=:tenant'), {'tenant': tenant}).mappings().one()
            previous = connection.execute(text('SELECT * FROM rag_generations WHERE tenant_id=:tenant AND id=:id'),
                                          {'tenant': tenant, 'id': head['previous_generation_id']}).mappings().first()
        if not previous or previous['catalog_revision'] != head['catalog_revision']:
            raise StaleGeneration('Rollback requires a verified rebuild over the current catalog')
        return self.activate(tenant, previous['id'], expected_head=expected_head, expected_version=expected_version,
                             authorize=authorize, _rollback=True)

    def rebuild_previous(self, tenant, provider, *, expected_head, expected_version, authorize=None):
        """Rollback after catalog changes rebuilds the prior recipe, never its old data."""
        with self.engine.connect() as connection:
            head = connection.execute(text('SELECT * FROM tenant_rag_head WHERE tenant_id=:tenant'), {'tenant': tenant}).mappings().one()
            previous = connection.execute(text('''SELECT g.*,s.descriptor FROM rag_generations g
                JOIN embedding_spaces s ON s.id=g.space_id WHERE g.tenant_id=:tenant AND g.id=:id'''),
                {'tenant': tenant, 'id': head['previous_generation_id']}).mappings().first()
        if head['generation_id'] != expected_head or head['version'] != expected_version or not previous:
            raise StaleGeneration('The previous index is unavailable or the head changed')
        candidate = self.build(tenant, EmbeddingSpace.from_descriptor(previous['descriptor']), provider,
                               retrieval_mode=previous['retrieval_config']['mode'], rrf_k=previous['retrieval_config']['rrf_k'], authorize=authorize)
        return self.activate(tenant, candidate, expected_head=expected_head, expected_version=expected_version, authorize=authorize)

    def inspect(self, tenant, generation=None):
        with self.engine.connect() as connection:
            rows = connection.execute(text('''SELECT g.id,g.space_id,g.state,g.catalog_revision,g.manifest,g.retrieval_config,
                g.created_at,g.retired_at,s.descriptor FROM rag_generations g JOIN embedding_spaces s ON s.id=g.space_id
                WHERE g.tenant_id=:tenant ''' + (' AND g.id=:id' if generation else '') + ' ORDER BY g.created_at,g.id'),
                {'tenant': tenant, 'id': generation}).mappings().all()
            result = []
            for row in rows:
                item = dict(row)
                try:
                    self._check_complete(connection, tenant, item['id'], item['space_id'], item['manifest']['chunk_count'])
                    self._check_manifest(connection, tenant, item['id'], item['manifest'])
                    item['complete'] = item['state'] in {'ready', 'retired'}
                except (KeyError, ValueError):
                    item['complete'] = False
                result.append(item)
        return {'head': self.active_plan(tenant), 'generations': result}

    def prune(self, tenant, *, keep=(), limit=10, grace_seconds=600, cache_age_seconds=604800, authorize=None):
        """Bounded operator maintenance. No cascade into canonical/legacy tables."""
        if (type(limit) is not int or not 1 <= limit <= 100 or type(grace_seconds) is not int or grace_seconds < 600
                or type(cache_age_seconds) is not int or cache_age_seconds < 600):
            raise ValueError('Unsafe retention limits')
        if authorize is not None: authorize()
        removed, retired = [], []
        with self.engine.begin() as connection:
            head = lock_head(connection, tenant)
            if authorize is not None: authorize()
            protected = set(keep) | {head['generation_id'], head['previous_generation_id']}
            rows = connection.execute(text("SELECT id,state,retired_at FROM rag_generations WHERE tenant_id=:tenant AND state<>'building' ORDER BY created_at,id FOR UPDATE"),
                                      {'tenant': tenant}).mappings().all()
            for row in rows:
                if row['id'] in protected or len(removed) + len(retired) >= limit: continue
                if row['retired_at'] is None:
                    connection.execute(text("UPDATE rag_generations SET state='retired',retired_at=clock_timestamp() WHERE tenant_id=:tenant AND id=:id"),
                                       {'tenant': tenant, 'id': row['id']})
                    retired.append(row['id'])
                    continue
                eligible = connection.execute(text("SELECT :retired < clock_timestamp() - make_interval(secs=>:grace)"),
                                              {'retired': row['retired_at'], 'grace': grace_seconds}).scalar_one()
                if not eligible: continue
                connection.execute(text('DELETE FROM rag_generation_members WHERE tenant_id=:tenant AND generation_id=:id'), {'tenant': tenant, 'id': row['id']})
                connection.execute(text('DELETE FROM rag_generations WHERE tenant_id=:tenant AND id=:id'), {'tenant': tenant, 'id': row['id']})
                removed.append(row['id'])
            # Only revisions with no retained generation membership can be reclaimed.
            unused = '''tenant_id=:tenant AND NOT EXISTS (SELECT 1 FROM rag_generation_members m
                WHERE m.tenant_id=rag_document_revisions.tenant_id AND m.revision_id=rag_document_revisions.id)'''
            revisions = list(connection.execute(text('SELECT id FROM rag_document_revisions WHERE ' + unused + ' ORDER BY created_at,id LIMIT :limit'),
                                                {'tenant': tenant, 'limit': limit}).scalars())
            for revision in revisions:
                params = {'tenant': tenant, 'revision': revision}
                connection.execute(text('DELETE FROM rag_chunk_vectors WHERE tenant_id=:tenant AND revision_id=:revision'), params)
                connection.execute(text('DELETE FROM rag_revision_chunks WHERE tenant_id=:tenant AND revision_id=:revision'), params)
                connection.execute(text('DELETE FROM rag_document_revisions WHERE tenant_id=:tenant AND id=:revision'), params)
            cache = connection.execute(text('''DELETE FROM embedding_cache WHERE (tenant_id,space_id,text_hash) IN
                (SELECT e.tenant_id,e.space_id,e.text_hash FROM embedding_cache e WHERE e.tenant_id=:tenant
                AND e.last_used_at < clock_timestamp() - make_interval(secs=>:age)
                AND NOT EXISTS(SELECT 1 FROM rag_chunk_vectors v WHERE v.tenant_id=e.tenant_id AND v.space_id=e.space_id AND v.text_hash=e.text_hash)
                ORDER BY e.last_used_at,e.space_id,e.text_hash LIMIT :limit)'''),
                {'tenant': tenant, 'age': cache_age_seconds, 'limit': limit}).rowcount
        return {'removed_generations': removed, 'retired_generations': retired, 'removed_revisions': len(revisions), 'removed_cache': cache}


def publication_chunks(document_id, chunks):
    return [{'chunk_id': item['chunk_id'], 'chunk_index': index, 'content': item['content'], 'metadata': item['metadata']}
            if isinstance(item, dict) else {'chunk_id': f'{document_id}:chunk:{index}', 'chunk_index': index,
                                          'content': item, 'metadata': {}} for index, item in enumerate(chunks)]
