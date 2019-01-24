from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('knowu2/', include('knowu2.urls')),
    path('', RedirectView.as_view(url='/knowu2/', permanent=True)),
 ]
