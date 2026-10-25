from importlib import import_module


def test_postgresql_catalog_any_is_equivalent_to_in():
    normalize = import_module('app.db.migrations.002_chat_operations').normalize
    assert normalize("state = ANY (ARRAY['active'::text, 'waiting'::text])") == normalize("state IN ('active','waiting')")


def test_postgresql_catalog_normalization_preserves_extra_predicates():
    normalize = import_module('app.db.migrations.002_chat_operations').normalize
    expected = normalize("state IN ('active','waiting')")
    assert normalize("state = ANY (ARRAY['active'::text, 'waiting'::text]) OR true") != expected
    assert normalize("state = ANY (ARRAY['active'::text, 'waiting'::text, 'forged'::text])") != expected
