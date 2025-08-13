# accounts/urls.py
from django.urls import path
from . import views
from .views import update_difficulty, register_view

urlpatterns = [
    path('update-difficulty/', update_difficulty, name='update_difficulty'),
    path('register/', register_view, name='register'),   # ✅ custom register page
    path('dashboard/', views.dashboard, name='dashboard'),
    path('premium-dashboard/', views.premium_dashboard, name='premium_dashboard'),
    path('logout/', views.logout_view, name='logout'),
]