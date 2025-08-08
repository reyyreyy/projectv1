from django.urls import path
from . import views
from .views import signup_view
from .views import redirect_after_login  # ✅ Add this at the top
from .views import custom_login
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('', views.generate_exercise, name='generate_exercise'),  # Homepage redirects to generate
	path('login/', auth_views.LoginView.as_view(template_name='exercises/login.html'), name='login'),
    path('generate/', views.generate_exercise, name='generate_exercise'),
    path('history/', views.exercise_history, name='exercise_history'),
    path('retry/', views.retry_exercise, name='retry_exercise'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
	path('signup/', signup_view, name='signup'),
	path('redirect-after-login/', redirect_after_login, name='redirect_after_login'),  # ✅ Add this line
	path('login/', custom_login, name='login'),
	path('', views.home_view, name='home'),  # this should be public
	
]

