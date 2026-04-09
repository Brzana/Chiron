"""
Tests for user endpoints (/users/me).
"""
import pytest
from fastapi.testclient import TestClient


class TestGetCurrentUser:
    """Tests for GET /users/me endpoint."""

    def test_get_me_success_student(self, client: TestClient, student_token: str, test_student_user):
        """Test getting current user info as student."""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_student_user.id
        assert data["username"] == "testuser"
        assert data["email"] == "student@example.com"
        assert data["role"] == "student"
        assert "created_at" in data

    def test_get_me_success_teacher(self, client: TestClient, teacher_token: str, test_teacher_user):
        """Test getting current user info as teacher."""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_teacher_user.id
        assert data["username"] == "testteacher"
        assert data["email"] == "teacher@example.com"
        assert data["role"] == "teacher"

    def test_get_me_success_admin(self, client: TestClient, admin_token: str, test_admin_user):
        """Test getting current user info as admin."""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_admin_user.id
        assert data["username"] == "testadmin"
        assert data["email"] == "admin@example.com"
        assert data["role"] == "admin"

    def test_get_me_fail_no_token(self, client: TestClient):
        """Test getting current user fails without token."""
        response = client.get("/api/users/me")
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "credentials_missing"

    def test_get_me_fail_invalid_token(self, client: TestClient):
        """Test getting current user fails with invalid token."""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        
        assert response.status_code == 401

    def test_get_me_fail_wrong_scheme(self, client: TestClient, student_token: str):
        """Test getting current user fails with wrong authentication scheme."""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Basic {student_token}"},
        )
        
        assert response.status_code == 401

    def test_get_me_fail_malformed_auth_header(self, client: TestClient):
        """Test getting current user fails with malformed auth header."""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": "InvalidHeader"},
        )
        
        assert response.status_code == 401

    def test_get_me_fail_expired_token(self, client: TestClient):
        """Test getting current user fails with expired token."""
        from packages.backend.core.security import create_access_token
        from datetime import timedelta, datetime, timezone
        
        # Create an already-expired token
        past_exp = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        expired_token = create_access_token(
            {"sub": "1", "role": "student"},
            expires_delta=timedelta(hours=-1),
        )
        
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        
        assert response.status_code == 401
