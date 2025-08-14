# ABOUT-ME: Tests for initializing a minimal SQLite database schema and basic CRUD.
# ABOUT-ME: Verifies the 'users' table exists and supports insert and query operations.

from sqlalchemy import inspect, select

from src.db import init_db, User


def test_init_db_creates_users_table_and_basic_crud():
    # Use in-memory SQLite for tests (isolated, ephemeral)
    engine, SessionLocal = init_db("sqlite:///:memory:")

    inspector = inspect(engine)
    assert inspector.has_table("users"), "Expected 'users' table to be created"

    # Basic CRUD: insert and fetch
    with SessionLocal() as session:
        u = User(username="alice")
        session.add(u)
        session.commit()
        session.refresh(u)
        assert u.id is not None

        row = session.execute(select(User).where(User.username == "alice")).scalar_one()
        assert row.id == u.id
