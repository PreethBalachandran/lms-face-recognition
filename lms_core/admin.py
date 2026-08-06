from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Course, Enrollment, CourseMaterial, Assignment, Submission


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'faculty', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name', 'faculty__username')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'enrolled_at')
    list_filter = ('status',)
    search_fields = ('student__username', 'course__code')

@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'uploaded_by', 'uploaded_at')
    list_filter = ('course',)
    search_fields = ('title', 'course__code')




@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'submitted_at', 'is_late')
    list_filter = ('is_late',)
    search_fields = ('student__username', 'assignment__title')