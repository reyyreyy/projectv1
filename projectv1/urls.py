from django.contrib import admin
from django.urls import path, include
from exercises.views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('exercises/', include('exercises.urls')),
    path('payments/', include('payments.urls')),
]