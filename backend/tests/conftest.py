import os

os.environ["DATABASE_URL"] = "sqlite:///./test_crm_fuel.db"
os.environ["DEV_AUTH_ENABLED"] = "true"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as value:
        yield value
    Base.metadata.drop_all(engine)

