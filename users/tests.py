from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class RegistrationSecurityTests(TestCase):
    """
    Confirms the security boundary: self-registration always creates a
    STUDENT, regardless of what role the client requests. This is the
    fix for a real vulnerability pattern (client-controlled privilege).
    """

    def setUp(self):
        self.client = APIClient()

    def test_register_ignores_requested_admin_role(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'sneaky_user',
            'email': 'sneaky@test.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'role': 'admin',  # attempting privilege escalation
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_user = User.objects.get(username='sneaky_user')
        self.assertEqual(created_user.role, 'student')

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='existing_user', password='pass123', role='student')
        response = self.client.post('/api/auth/register/', {
            'username': 'existing_user',
            'email': 'new@test.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RoleBasedPermissionTests(TestCase):
    """Confirms students genuinely cannot reach admin-only endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(username='a_student', password='pass123', role='student')

    def test_student_cannot_create_faculty_account(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post('/api/auth/admin/create-user/', {
            'username': 'fake_faculty',
            'email': 'fake@test.com',
            'password': 'Pass123!',
            'role': 'faculty',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)