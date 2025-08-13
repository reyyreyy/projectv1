from django.contrib import admin
from django.urls import path, include
from exercises.views import dashboard_router  # or home_view if you prefer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_router, name='home'),            # role-based landing
    path('accounts/', include('accounts.urls')),        # our register view
    path('exercises/', include('exercises.urls')),
    path('payments/', include('payments.urls')),        # optional
]