"""Shared pytest fixtures for Opentill backend tests."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from backend.database import get_session
from backend.main import app

# Import all table models to register them
from backend.catalog.infrastructure.sqlmodel_models import ProductTable  # noqa
from backend.sales.infrastructure.sqlmodel_models import OrderTable, OrderItemTable  # noqa


@pytest.fixture(name="session")
def session_fixture():
    """In-memory SQLite session for tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """FastAPI TestClient with overridden DB session."""
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_product_data():
    return {
        "name": "Test Product",
        "sku": "TEST-001",
        "price": 9.99,
        "tax_rate": 0.21,
        "barcode": "1234567890123",
        "cost": 5.00,
        "stock": 10,
        "category": "General",
        "description": "A test product",
        "currency": "EUR",
    }
