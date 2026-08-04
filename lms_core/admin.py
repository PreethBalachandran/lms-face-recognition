from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Course, Enrollment


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