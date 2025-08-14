from django.contrib import admin
from django.urls import path, include
from exercises.views import home_view
from accounts.views import login_view, register_view, logout_view

urlpatterns = [
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('admin/', admin.site.urls),
    path('exercises/', include('exercises.urls')),
    path('payments/', include('payments.urls')),        
]