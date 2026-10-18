from pathlib import Path

# The backend and the processor ship separate images, so the pure chat modules are copies.
# chat_resources.py packages/verifies each service's different token resources.
SERVICE_SPECIFIC = {'chat_resources.py'}
# Admission owns processor-only in-memory concurrency; backend has no such gate.
PROCESSOR_ONLY = {'chat_admission.py'}


def test_every_chat_module_present_in_both_services_is_byte_identical():
    root = Path(__file__).resolve().parents[3] / 'apps'
    backend, processor = (root / service / 'app/core' for service in ('backend', 'processor'))
    backend_names = {path.name for path in backend.glob('chat_*.py')} - SERVICE_SPECIFIC
    processor_names = {path.name for path in processor.glob('chat_*.py')} - SERVICE_SPECIFIC - PROCESSOR_ONLY
    assert all((processor / name).is_file() and not (backend / name).exists() for name in PROCESSOR_ONLY)
    assert backend_names == processor_names
    shared = sorted(backend_names)
    assert len(shared) >= 22, shared
    assert [name for name in shared if (backend / name).read_bytes() != (processor / name).read_bytes()] == []
