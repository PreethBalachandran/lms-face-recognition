from rest_framework import serializers
from .models import Course, Enrollment, CourseMaterial, Assignment, Submission


class CourseSerializer(serializers.ModelSerializer):
    faculty_username = serializers.CharField(source='faculty.username', read_only=True)
    enrolled_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'name', 'code', 'description', 'faculty', 'faculty_username',
            'is_active', 'created_at', 'enrolled_count',
        ]
        read_only_fields = ['id', 'faculty', 'created_at']

    def get_enrolled_count(self, obj):
        return obj.enrollments.filter(status='active').count()


class EnrollmentSerializer(serializers.ModelSerializer):
    student_username = serializers.CharField(source='student.username', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'student_username', 'course', 'course_name',
            'course_code', 'status', 'enrolled_at',
        ]
        read_only_fields = ['id', 'student', 'enrolled_at']

class CourseMaterialSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)

    class Meta:
        model = CourseMaterial
        fields = [
            'id', 'course', 'title', 'file', 'description', 'order',
            'uploaded_by', 'uploaded_by_username', 'uploaded_at',
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']

class AssignmentSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.code', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            'id', 'course', 'course_code', 'title', 'description', 'max_marks',
            'due_date', 'created_by', 'created_by_username', 'created_at', 'is_overdue',
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_is_overdue(self, obj):
        from django.utils import timezone
        return timezone.now() > obj.due_date

class SubmissionSerializer(serializers.ModelSerializer):
    student_username = serializers.CharField(source='student.username', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id', 'assignment', 'assignment_title', 'student', 'student_username',
            'file', 'submitted_at', 'is_late',
        ]
        read_only_fields = ['id', 'student', 'submitted_at', 'is_late']



class SubmissionSerializer(serializers.ModelSerializer):
    student_username = serializers.CharField(source='student.username', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    graded_by_username = serializers.CharField(source='graded_by.username', read_only=True, default=None)
    is_graded = serializers.BooleanField(read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id', 'assignment', 'assignment_title', 'student', 'student_username',
            'file', 'submitted_at', 'is_late', 'marks_obtained', 'feedback',
            'graded_by', 'graded_by_username', 'graded_at', 'is_graded',
        ]
        read_only_fields = ['id', 'student', 'submitted_at', 'is_late', 'graded_by', 'graded_at']