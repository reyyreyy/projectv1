from django.contrib import admin
from django.urls import path, include
from accounts.views import login_view, register_view, logout_view
from exercises.views import home_view
from django.http import HttpResponse

def healthz(_request):
    return HttpResponse("ok")


urlpatterns = [
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path("healthz/", healthz),
    path('accounts/', include('accounts.urls')),
    path('admin/', admin.site.urls),
]