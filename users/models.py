from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Extends Django's built-in user with a `role` field.
    Role drives permissions across every other app (attendance, lms_core).
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        FACULTY = 'faculty', 'Faculty'
        STUDENT = 'student', 'Student'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    phone_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_faculty(self):
        return self.role == self.Role.FACULTY

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT