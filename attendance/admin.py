from django.contrib import admin
from .models import FaceEncoding, AttendanceSession, AttendanceRecord


@admin.register(FaceEncoding)
class FaceEncodingAdmin(admin.ModelAdmin):
    list_display = ('student', 'enrolled_at', 'updated_at')
    search_fields = ('student__username',)


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('course_name', 'session_type', 'faculty', 'session_date', 'is_open', 'start_time', 'end_time')
    list_filter = ('session_type', 'is_open', 'session_date')
    search_fields = ('course_name', 'faculty__username')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'is_present', 'marked_via', 'marked_at', 'confidence_score')
    list_filter = ('is_present', 'marked_via')
    search_fields = ('student__username',)