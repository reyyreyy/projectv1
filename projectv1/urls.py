from django.contrib import admin
from django.urls import path
from accounts.views import login_view, register_view, logout_view
from exercises.views import home_view, student_dashboard

urlpatterns = [
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('exercises/student-dashboard/', student_dashboard, name='student_dashboard'),
    path('admin/', admin.site.urls),
]