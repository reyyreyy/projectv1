from django.urls import path, include
from .views import logout_view, update_difficulty, register_view

urlpatterns = [
    path('logout/', logout_view, name='logout'),  # our override FIRST
    path('update-difficulty/', update_difficulty, name='update_difficulty'),
    path('register/', register_view, name='register'),   # ✅ custom register page
    path('dashboard/', views.dashboard, name='dashboard'),
    path('premium-dashboard/', views.premium_dashboard, name='premium_dashboard'),
    path('', include('django.contrib.auth.urls')),
]