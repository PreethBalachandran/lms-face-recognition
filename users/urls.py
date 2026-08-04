from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='login-refresh'),
    path('me/', views.MeView.as_view(), name='me'),
    path('admin/create-user/', views.AdminCreateUserView.as_view(), name='admin-create-user'),
    path('admin/users/', views.AdminUserListView.as_view(), name='admin-user-list'),
]