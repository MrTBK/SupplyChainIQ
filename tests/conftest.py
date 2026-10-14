import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(scope="session", autouse=True)
def _ensure_warehouse_fallback(tmp_path_factory):
    import api.config as cfg
    import api.db as dbmod
    if not cfg.WAREHOUSE_DB.exists():
        from tests.api_fixtures import build_warehouse
        wh_dir = tmp_path_factory.mktemp("wh")
        db = build_warehouse(wh_dir)
        cfg.WAREHOUSE_DB = db
        dbmod.WAREHOUSE_DB = db

