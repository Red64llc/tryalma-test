# Python FastAPI Standards

REST APIs built with FastAPI, featuring layered architecture, Pydantic v2 validation, JWT authentication, and async SQLAlchemy.

---

## Framework: FastAPI

Use [FastAPI](https://fastapi.tiangolo.com/) for all REST APIs.

```python
from fastapi import FastAPI

app = FastAPI(
    title="My API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
```

### Key Principles

- Async-first: Use `async def` for all route handlers
- Type hints everywhere: Enables automatic validation and documentation
- Dependency injection: Decouple components for testability
- Pydantic models: Define contracts, not just validation

---

## Project Structure (Layered)

```
src/
  api/
    v1/
      __init__.py
      router.py          # Aggregates all v1 routers
      users.py           # User endpoints
      items.py           # Item endpoints
    deps.py              # Shared dependencies (auth, db session)
  core/
    config.py            # Settings via pydantic-settings
    security.py          # JWT utilities
  models/
    user.py              # SQLAlchemy models
    item.py
  schemas/
    user.py              # Pydantic request/response schemas
    item.py
    common.py            # Shared schemas (pagination, errors)
  services/
    user_service.py      # Business logic
    item_service.py
  repositories/
    user_repo.py         # Data access layer
    item_repo.py
  exceptions.py          # Custom exception hierarchy
  main.py                # App factory, startup/shutdown
```

### Layer Responsibilities

| Layer | Responsibility |
|-------|----------------|
| **Routers** | HTTP handling, request parsing, response formatting |
| **Services** | Business logic, orchestration, validation rules |
| **Repositories** | Data access, queries, persistence |
| **Schemas** | Request/response contracts (Pydantic) |
| **Models** | Database entities (SQLAlchemy) |

---

## Endpoint Pattern

### URL Structure

```
/api/v1/{resource}[/{id}][/{sub-resource}]
```

Examples:
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user
- `GET /api/v1/users/{id}/orders` - User's orders

### Router Definition

```python
# api/v1/users.py
from fastapi import APIRouter, Depends, status
from src.schemas.user import UserCreate, UserResponse, UserList
from src.services.user_service import UserService
from src.api.deps import get_user_service, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=UserList)
async def list_users(
    skip: int = 0,
    limit: int = 20,
    service: UserService = Depends(get_user_service),
):
    """List all users with pagination."""
    return await service.list_users(skip=skip, limit=limit)

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    service: UserService = Depends(get_user_service),
):
    """Create a new user."""
    return await service.create_user(user_in)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """Get user by ID."""
    return await service.get_user(user_id)
```

### Router Aggregation

```python
# api/v1/router.py
from fastapi import APIRouter
from src.api.v1 import users, items

router = APIRouter(prefix="/api/v1")
router.include_router(users.router)
router.include_router(items.router)
```

---

## Pydantic Schemas (v2)

### Schema Conventions

```python
# schemas/user.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    """Shared user attributes."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)

class UserCreate(UserBase):
    """Request schema for creating user."""
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    """Response schema for user."""
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class UserList(BaseModel):
    """Paginated user list response."""
    items: list[UserResponse]
    total: int
    skip: int
    limit: int
```

### Strict Validation

```python
from pydantic import BaseModel, ConfigDict

class StrictSchema(BaseModel):
    """Base for strict validation (no coercion)."""
    model_config = ConfigDict(strict=True)
```

---

## Dependency Injection

### Database Session

```python
# api/deps.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import async_session_maker

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
```

### Service Dependencies

```python
# api/deps.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.user_service import UserService
from src.repositories.user_repo import UserRepository

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)
```

### Dependency Chain Pattern

```
Request -> Router -> Depends(get_service) -> Service(repo) -> Repository(db)
```

Each layer receives its dependencies; no direct instantiation in routers.

---

## Authentication (JWT)

### Security Utilities

```python
# core/security.py
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
```

### Auth Dependency

```python
# api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from src.core.config import settings
from src.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: UserService = Depends(get_user_service),
):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = await service.get_user(int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user
```

### Protected Routes

```python
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    return current_user
```

---

## Error Handling

### Exception Hierarchy

```python
# exceptions.py
from fastapi import status

class APIError(Exception):
    """Base API exception."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)

class NotFoundError(APIError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"
    message = "Resource not found"

class ValidationError(APIError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "VALIDATION_ERROR"
    message = "Validation failed"

class AuthenticationError(APIError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "AUTHENTICATION_ERROR"
    message = "Authentication required"

class AuthorizationError(APIError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "AUTHORIZATION_ERROR"
    message = "Permission denied"
```

### Exception Handlers

```python
# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.exceptions import APIError

app = FastAPI()

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )
```

### Error Response Format

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "User not found"
  }
}
```

### Raising Errors in Services

```python
# services/user_service.py
from src.exceptions import NotFoundError

class UserService:
    async def get_user(self, user_id: int) -> User:
        user = await self.repo.get(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user
```

---

## Database (SQLAlchemy Async)

### Session Factory

```python
# core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

### Repository Pattern

```python
# repositories/user_repo.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
```

---

## Testing (API-Specific)

For general TDD principles, see [python-tdd.md](./python-tdd.md).

### TestClient Setup

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.main import app
from src.api.deps import get_db

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession)

@pytest.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

### API Test Pattern

```python
# tests/api/test_users.py
import pytest

@pytest.mark.asyncio
async def test_create_user_returns_201(client):
    response = await client.post(
        "/api/v1/users",
        json={"email": "test@example.com", "name": "Test", "password": "securepass123"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_nonexistent_user_returns_404(client):
    response = await client.get("/api/v1/users/9999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
```

### Auth Test Fixtures

```python
# tests/conftest.py
from src.core.security import create_access_token

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}

# Usage
@pytest.mark.asyncio
async def test_protected_endpoint(client, auth_headers):
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
```

---

## Anti-Patterns to Avoid

### 1. Business Logic in Routers

```python
# Bad: Logic in router
@router.post("/users")
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Email exists")
    user = User(**user_in.dict())
    db.add(user)
    await db.commit()
    return user

# Good: Delegate to service
@router.post("/users")
async def create_user(user_in: UserCreate, service: UserService = Depends(get_user_service)):
    return await service.create_user(user_in)
```

### 2. Direct HTTPException in Services

```python
# Bad: HTTP concerns in service
class UserService:
    async def get_user(self, user_id: int):
        user = await self.repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404)  # HTTP in service!
        return user

# Good: Domain exceptions
class UserService:
    async def get_user(self, user_id: int):
        user = await self.repo.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user
```

### 3. Missing Response Models

```python
# Bad: No response model (leaks internal fields)
@router.get("/users/{id}")
async def get_user(id: int):
    return await service.get_user(id)

# Good: Explicit response model
@router.get("/users/{id}", response_model=UserResponse)
async def get_user(id: int):
    return await service.get_user(id)
```

---

_Focus on patterns and conventions. Endpoint catalogs belong in specs._
