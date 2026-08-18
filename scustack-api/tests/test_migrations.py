from alembic.config import Config
from alembic.script import ScriptDirectory


def test_migration_history_has_one_unique_head():
    script = ScriptDirectory.from_config(Config('alembic.ini'))
    revisions = list(script.walk_revisions())
    revision_ids = [revision.revision for revision in revisions]

    assert len(revision_ids) == len(set(revision_ids))
    assert script.get_heads() == ['032']
