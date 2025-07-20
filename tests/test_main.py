import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from typing import AsyncGenerator

from app.main import app, get_db
from app.database import Base

TEST_DB = "test_books.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///./{TEST_DB}"

@pytest_asyncio.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncSession, None]:
    _engine = create_async_engine(TEST_DATABASE_URL)
    yield _engine
    await _engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    del app.dependency_overrides[get_db]

@pytest.mark.asyncio
async def test_create_and_read_book(client: AsyncClient):
    # Create a book
    response = await client.post(
        "/books/",
        json={"title": "Test Book", "author": "Test Author", "published_year": 2023, "summary": "A test summary."}
    )
    assert response.status_code == 201
    created_data = response.json()
    assert created_data["title"] == "Test Book"
    assert "id" in created_data
    book_id = created_data["id"]

    # Read the book back
    response = await client.get(f"/books/{book_id}")
    assert response.status_code == 200
    read_data = response.json()
    assert read_data == created_data

@pytest.mark.asyncio
async def test_read_books(client: AsyncClient):
    await client.post("/books/", json={"title": "Book 1", "author": "Author 1", "published_year": 2021})
    await client.post("/books/", json={"title": "Book 2", "author": "Author 2", "published_year": 2022})
    
    response = await client.get("/books/")
    assert response.status_code == 200
    assert len(response.json()) == 2

@pytest.mark.asyncio
async def test_update_book(client: AsyncClient):
    response = await client.post("/books/", json={"title": "Old Title", "author": "Old Author", "published_year": 2000})
    book_id = response.json()["id"]

    response = await client.put(f"/books/{book_id}", json={"title": "New Title"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["author"] == "Old Author"

@pytest.mark.asyncio
async def test_delete_book(client: AsyncClient):
    response = await client.post("/books/", json={"title": "To Be Deleted", "author": "Author", "published_year": 2023})
    book_id = response.json()["id"]

    # Delete the book
    response = await client.delete(f"/books/{book_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(f"/books/{book_id}")
    assert response.status_code == 404

# Cleanup test database file after all tests are done
@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Cleanup a testing database"""
    def remove_test_db():
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
    request.addfinalizer(remove_test_db) 