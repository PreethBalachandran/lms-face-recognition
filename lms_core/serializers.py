from rest_framework import serializers
from .models import Course, Enrollment, CourseMaterial


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