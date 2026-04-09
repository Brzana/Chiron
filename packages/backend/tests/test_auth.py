"""
Tests for authentication endpoints (/auth/register, /auth/login).
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthRegister:
    """Tests for user registration endpoint."""

    def test_register_success_student(self, client: TestClient):
        """Test successful student registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newstudent",
                "email": "newstudent@example.com",
                "password": "NewPassword123",
                "role": "student",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_success_teacher(self, client: TestClient):
        """Test successful teacher registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newteacher",
                "email": "newteacher@example.com",
                "password": "TeacherPass123",
                "role": "teacher",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_fail_admin_role(self, client: TestClient):
        """Test registration fails when trying to register as admin."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "adminuser",
                "email": "admin@example.com",
                "password": "AdminPass123",
                "role": "admin",
            },
        )
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_register_fail_duplicate_username(self, client: TestClient, test_student_user):
        """Test registration fails with duplicate username."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",  # Already exists
                "email": "different@example.com",
                "password": "NewPassword123",
                "role": "student",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "duplicate_field"
        assert "Username" in data["detail"]["message"]

    def test_register_fail_duplicate_email(self, client: TestClient, test_student_user):
        """Test registration fails with duplicate email."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newusername",
                "email": "student@example.com",  # Already exists
                "password": "NewPassword123",
                "role": "student",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "duplicate_field"
        assert "Email" in data["detail"]["message"]

    def test_register_fail_short_username(self, client: TestClient):
        """Test registration fails with username too short."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "ab",  # Too short
                "email": "test@example.com",
                "password": "NewPassword123",
                "role": "student",
            },
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_register_fail_short_password(self, client: TestClient):
        """Test registration fails with password too short."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "test@example.com",
                "password": "Short1",  # Too short
                "role": "student",
            },
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_register_fail_invalid_email(self, client: TestClient):
        """Test registration fails with invalid email."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "invalid-email",  # Invalid email
                "password": "NewPassword123",
                "role": "student",
            },
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestAuthLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, client: TestClient, test_student_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "student@example.com",
                "password": "TestPassword123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_fail_invalid_email(self, client: TestClient):
        """Test login fails with non-existent email."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "TestPassword123",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "invalid_credentials"
        assert "Invalid email or password" in data["detail"]["message"]

    def test_login_fail_wrong_password(self, client: TestClient, test_student_user):
        """Test login fails with wrong password."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "student@example.com",
                "password": "WrongPassword123",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "invalid_credentials"
        assert "Invalid email or password" in data["detail"]["message"]

    def test_login_fail_invalid_email_format(self, client: TestClient):
        """Test login fails with invalid email format."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "invalid-email",
                "password": "TestPassword123",
            },
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_login_teacher(self, client: TestClient, test_teacher_user):
        """Test successful teacher login."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "teacher@example.com",
                "password": "TeacherPass123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_admin(self, client: TestClient, test_admin_user):
        """Test successful admin login."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@example.com",
                "password": "AdminPass123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
