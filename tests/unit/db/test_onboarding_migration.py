from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

from sqlalchemy import Column


class _OperationsSpy:
    def __init__(self) -> None:
        self.columns: list[tuple[str, Column[object]]] = []
        self.sql: list[str] = []

    def add_column(self, table: str, column: Column[object]) -> None:
        self.columns.append((table, column))

    def execute(self, statement: str) -> None:
        self.sql.append(statement)


def _load_migration() -> ModuleType:
    path = (
        Path(__file__).resolve().parents[3]
        / "alembic"
        / "versions"
        / "a4b5c6d7e8f9_add_server_side_onboarding.py"
    )
    spec = spec_from_file_location("test_onboarding_migration_module", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_is_additive_and_old_backend_columns_remain_compatible(monkeypatch) -> None:
    migration = _load_migration()
    operations = _OperationsSpy()
    monkeypatch.setattr(migration, "op", operations)

    migration.upgrade()

    assert [column.name for _, column in operations.columns] == [
        "cv_work_formats",
        "onboarding_draft",
        "onboarding_completed_at",
    ]
    assert all(column.nullable is True for _, column in operations.columns)
    assert all(column.server_default is None for _, column in operations.columns)
    assert not any("DROP COLUMN" in statement.upper() for statement in operations.sql)
    assert not any("ALTER COLUMN" in statement.upper() for statement in operations.sql)


def test_migration_installs_temporary_legacy_writer_trigger(monkeypatch) -> None:
    migration = _load_migration()
    operations = _OperationsSpy()
    monkeypatch.setattr(migration, "op", operations)

    migration.upgrade()

    sql = "\n".join(operations.sql)
    assert "trg_users_legacy_work_format_compat" in sql
    assert "NEW.cv_work_formats IS NOT DISTINCT FROM OLD.cv_work_formats" in sql
    assert "jsonb_build_array(NEW.cv_work_format)" in sql
    assert "ELSE '[]'::jsonb" in sql
    assert "UPDATE OF cv_work_format, filter_work_format_mode, cv_work_formats" in sql


def test_backfill_maps_only_strict_valid_scalar_to_singleton(monkeypatch) -> None:
    migration = _load_migration()
    operations = _OperationsSpy()
    monkeypatch.setattr(migration, "op", operations)

    migration.upgrade()

    backfill = next(statement for statement in operations.sql if "UPDATE users" in statement)
    assert "filter_work_format_mode = 'STRICT'" in backfill
    assert "cv_work_format IS NOT NULL" in backfill
    assert "cv_work_format <> 'UNDEFINED'" in backfill
    assert "THEN jsonb_build_array(cv_work_format)" in backfill
    assert "ELSE '[]'::jsonb" in backfill
