"""Resource-backed token counts, ordinary special strings and fail-closed offline loading."""
from pathlib import Path
import pytest
from app.embeddings.tokenization import EmbeddingTokenCounter
from app.embeddings.tokenizer_resource import RESOURCE_SHA256, resource_path, assert_external_resource_path


def test_real_pinned_counter_is_deterministic_and_counts_the_effective_content():
    counter=EmbeddingTokenCounter()
    assert counter.count('hello world')==2
    assert counter.count('Presupuesto € 漢字 🙂\n')==counter.count('Presupuesto € 漢字 🙂\n')
    assert counter.count('<|endoftext|>')>1  # User text is not an executable special token.
    assert RESOURCE_SHA256 in counter.identity
    assert resource_path().is_file()
    with pytest.raises(UnicodeEncodeError): counter.count('bad\ud800')


def test_missing_bad_and_symlink_resource_never_try_a_network_constructor(tmp_path,monkeypatch):
    def forbidden(*_args,**_kwargs): pytest.fail('Resource loading must not access network')
    monkeypatch.setattr('requests.get',forbidden)
    with pytest.raises(ValueError): EmbeddingTokenCounter(tmp_path/'missing.tiktoken')
    wrong=tmp_path/'wrong.tiktoken'; wrong.write_bytes(b'wrong')
    with pytest.raises(ValueError): EmbeddingTokenCounter(wrong)
    symlink=tmp_path/'symlink.tiktoken'; symlink.symlink_to(resource_path())
    with pytest.raises(ValueError): EmbeddingTokenCounter(symlink)


def test_resource_default_is_outside_the_checkout(monkeypatch):
    monkeypatch.delenv('EMBEDDING_TOKENIZER_FILE',raising=False)
    root=Path(__file__).resolve().parents[3]
    assert not resource_path().resolve().is_relative_to(root)
    with pytest.raises(ValueError): assert_external_resource_path(root/'cl100k_base.tiktoken')


def test_missing_resource_reaches_startup_with_its_own_reason(tmp_path):
    from app.core.runtime_secrets import StartupError, startup_boundary
    @startup_boundary
    def start():
        EmbeddingTokenCounter(tmp_path/'missing.tiktoken')
    with pytest.raises(StartupError, match='Embedding tokenizer resource is missing.*build_tokenizer.py'):
        start()


@pytest.mark.parametrize('failure', ['version', 'hash'])
def test_invalid_tokenizer_keeps_the_closed_startup_reason(tmp_path, monkeypatch, failure):
    from app.core.runtime_secrets import StartupError, startup_boundary
    from app.embeddings import tokenization
    from app.embeddings.tokenizer_resource import RESOURCE_BYTES
    wrong = tmp_path/'wrong.tiktoken'
    if failure == 'version':
        monkeypatch.setattr(tokenization, 'version', lambda _: 'wrong-version')
        expected = 'library version mismatch'
    else:
        wrong.write_bytes(b'x' * RESOURCE_BYTES)
        expected = 'does not match the pinned SHA256'
    monkeypatch.setattr('requests.get', lambda *_args, **_kwargs: pytest.fail('No runtime network'))
    @startup_boundary
    def start():
        EmbeddingTokenCounter(wrong)
    with pytest.raises(StartupError, match=expected) as caught:
        start()
    assert isinstance(caught.value, ValueError)
