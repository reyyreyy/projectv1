from django.urls import path
from . import views
from .views import redirect_after_login  # ✅ Add this at the top
from .views import custom_login
from django.contrib.auth import views as auth_views
from .views import teacher_dashboard, update_student_level
from .views import (
    dashboard_router,
    admin_dashboard,
    teacher_dashboard,
    student_dashboard,
	)
urlpatterns = [
	path('', dashboard_router, name='home'),  # root redirects to proper dashboard
	path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
	path('teacher-dashboard/', teacher_dashboard, name='teacher_dashboard'),
	path('student-dashboard/', student_dashboard, name='student_dashboard'),
    path('', views.generate_exercise, name='generate_exercise'),  # Homepage redirects to generate
	path('login/', auth_views.LoginView.as_view(template_name='exercises/login.html'), name='login'),
    path('generate/', views.generate_exercise, name='generate_exercise'),
    path('history/', views.exercise_history, name='exercise_history'),
    path('retry/', views.retry_exercise, name='retry_exercise'),
	path('update-level/<int:profile_id>/', update_student_level, name='update_student_level'),
	path('redirect-after-login/', redirect_after_login, name='redirect_after_login'),  # ✅ Add this line
	path('login/', custom_login, name='login'),
	path('', views.home_view, name='home'),  # this should be public
]