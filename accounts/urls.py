from django.urls import path, include
from .views import logout_view

app_name = 'accounts'

urlpatterns = [
    path('logout/', logout_view, name='logout'),   # our override FIRST
    path('', include('django.contrib.auth.urls')), # then auth (login, password, etc.)
]