from django.db import models
from django.conf import settings


class Course(models.Model):
    """One row per course. Owned by exactly one faculty member."""
    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_taught',
        limit_choices_to={'role': 'faculty'},
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True, help_text="e.g. CS301")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} — {self.name}"


class Enrollment(models.Model):
    """
    Through-model connecting a student to a course.
    Not a plain ManyToManyField because we need extra data:
    WHEN they enrolled, and whether they're still active.
    """
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        DROPPED = 'dropped', 'Dropped'
        COMPLETED = 'completed', 'Completed'

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'student'},
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'course']  # can't enroll twice in the same course
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.username} in {self.course.code} ({self.status})"


class CourseMaterial(models.Model):
    """A file/note attached to a course — notes, slides, readings, etc."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='course_materials/%Y/%m/')
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Controls display order, e.g. Week 1 = 1")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_materials',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-uploaded_at']

    def __str__(self):
        return f"{self.course.code} — {self.title}"

class Assignment(models.Model):
    """An assignment posted for a course, with a due date."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    max_marks = models.PositiveIntegerField(default=100)
    due_date = models.DateTimeField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_assignments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.course.code} — {self.title} (due {self.due_date.date()})"