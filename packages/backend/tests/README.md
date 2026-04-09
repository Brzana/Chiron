# Backend Tests

This directory contains comprehensive tests for the Chiron backend API using pytest and pytest-asyncio.

## Test Structure

The tests are organized into three main test files:

### 1. `test_auth.py` - Authentication Tests

Tests for user registration and login endpoints:

- **TestAuthRegister**: Tests for `/api/auth/register` endpoint
  - Successful registration for student and teacher roles
  - Validation of password and username requirements
  - Duplicate username/email detection
  - Admin role registration prevention
- **TestAuthLogin**: Tests for `/api/auth/login` endpoint
  - Successful login for all user roles
  - Invalid email/password handling
  - Authentication error responses

### 2. `test_users.py` - User Endpoint Tests

Tests for user profile endpoints:

- **TestGetCurrentUser**: Tests for `/api/users/me` endpoint
  - Retrieving current user info for all roles
  - Authentication requirement validation
  - Invalid/expired token handling
  - Bearer token scheme validation

### 3. `test_courses.py` - Course Endpoint Tests

Tests for course management endpoints:

- **TestGetCourses**: Tests for `GET /api/courses`
  - Course retrieval by user role (student, teacher, admin)
  - Role-based filtering
- **TestCreateCourse**: Tests for `POST /api/courses`
  - Successful course creation by teachers
  - Authorization/authentication checks
  - Duplicate title validation
  - Published/unpublished course creation
- **TestUpdateCourse**: Tests for `PUT /api/courses/{course_id}`
  - Course updates by owner teacher
  - Admin override permissions
  - Partial updates
  - Authorization checks
  - 404 error handling

## Setup and Installation

### Prerequisites

- Python 3.10+
- pip

### Install Dependencies

```bash
cd packages/backend
pip install -r requirements.txt
```

The requirements.txt includes:

- `pytest==9.0.2` - Testing framework
- `pytest-asyncio==1.3.0` - Async test support
- `aiosqlite==0.20.0` - In-memory SQLite for testing
- All other backend dependencies

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Specific Test File

```bash
pytest tests/test_auth.py
```

### Run Specific Test Class

```bash
pytest tests/test_auth.py::TestAuthRegister
```

### Run Specific Test Function

```bash
pytest tests/test_auth.py::TestAuthRegister::test_register_success_student
```

### Run Tests by Marker

```bash
pytest -m auth
pytest -m courses
```

### Run with Coverage

```bash
pytest --cov=packages.backend --cov-report=html
```

### Run Tests in Parallel

```bash
pip install pytest-xdist
pytest -n auto
```

## Test Fixtures

The tests use fixtures defined in `conftest.py` to manage test data:

### Database Fixtures

- `test_db`: Creates an in-memory SQLite database for testing
- `override_get_db`: Overrides the database dependency for FastAPI
- `client`: Provides a TestClient with the overridden database

### User Fixtures

- `test_student_user`: Creates a test student user
- `test_teacher_user`: Creates a test teacher user
- `test_admin_user`: Creates a test admin user

### Authentication Fixtures

- `student_token`: JWT token for a student
- `teacher_token`: JWT token for a teacher
- `admin_token`: JWT token for an admin

### Course Fixtures

- `test_course`: Creates a published test course
- `test_unpublished_course`: Creates an unpublished test course

## Test Database

Tests use an in-memory SQLite database for isolation and speed. Each test gets:

- A fresh database instance
- Automatic cleanup after each test
- All tables created from the SQLAlchemy models

## Best Practices for Contributing Tests

1. **Use Descriptive Names**: Test methods should clearly describe what they test
2. **One Assertion Focus**: Each test should focus on one specific behavior
3. **Use Fixtures**: Leverage existing fixtures instead of creating data inline
4. **Test Error Cases**: Include tests for both success and failure paths
5. **Follow AAA Pattern**: Arrange data, Act on it, Assert results
6. **Add Docstrings**: Explain what each test validates

## Common Test Patterns

### Testing with Authentication

```python
def test_endpoint_requires_auth(self, client: TestClient):
    response = client.get("/api/protected-endpoint")
    assert response.status_code == 403

def test_endpoint_with_auth(self, client: TestClient, student_token: str):
    response = client.get(
        "/api/protected-endpoint",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 200
```

### Testing with Database Fixtures

```python
def test_with_existing_data(self, client: TestClient, test_student_user):
    # Fixture automatically creates user in test database
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    data = response.json()
    assert data["id"] == test_student_user.id
```

### Testing Validation

```python
def test_validation_error(self, client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "Pass123",
        }
    )
    assert response.status_code == 422  # Validation error
```

## Troubleshooting

### Tests Fail with "Module Not Found"

Make sure you're running pytest from the backend directory:

```bash
cd packages/backend
pytest
```

### Async Tests Hang

Ensure you have pytest-asyncio configured. The `pytest.ini` file sets `asyncio_mode = auto`.

### Database Conflicts

Tests use an in-memory database, so there should be no conflicts. If you see database errors:

1. Clear any `.pytest_cache` folder
2. Ensure no other tests are running in parallel on the same session
3. Check that database fixtures are properly using async/await

### Token-Related Failures

Make sure the JWT secret is configured in your `.env`. Tests use the same security settings as the main app.
