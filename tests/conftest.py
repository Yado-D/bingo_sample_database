import os
import tempfile
import shutil
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

import app.main as main_app
import app.database as app_db
from app.database import Base


@pytest.fixture(scope="session")
def tmp_sqlite_file(tmp_path_factory):
    path = tmp_path_factory.mktemp("data") / "test.db"
    return str(path)


@pytest.fixture(scope="session")
def engine(tmp_sqlite_file):
    url = f"sqlite:///{tmp_sqlite_file}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    return engine


@pytest.fixture(scope="session")
def SessionLocal(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def setup_database(engine, SessionLocal):
    # patch the app's core database engine/session to use the test sqlite engine
    # app.database re-exports the core database module; override its SessionLocal and engine
    import app.core.database as core_db

    core_db.engine = engine
    core_db.SessionLocal = SessionLocal

    # ensure get_db yields sessions from test SessionLocal
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    core_db.get_db = override_get_db

    # create all tables on the test engine
    Base.metadata.create_all(bind=engine)

    # override dependency in FastAPI app
    main_app.app.dependency_overrides[app_db.get_db] = override_get_db

    yield

    # teardown: drop all tables and remove file
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(setup_database):
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session(setup_database, SessionLocal):
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def create_user(db_session):
    from app import models, utils

    def _create(phone: str, password: str, role: models.Role, remaining_balance: float = 0.0, name: str = None):
        hashed = utils.hash_password(password)
        user = models.User(
            first_name=(name or phone),
            last_name=None,
            phone=phone,
            phone_number=phone,
            password=hashed,
            role=role,
            city=None,
            region=None,
            wallet_balance=remaining_balance,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create


@pytest.fixture
def get_token(client):
    def _get(phone: str, password: str):
        data = {"phone_number": phone, "password": password}
        resp = client.post("/auth/signin", json=data)
        assert resp.status_code == 200
        body = resp.json()
        return body["data"]["token"]

    return _get
