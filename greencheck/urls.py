from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from pages.views import home
from accounts.views import login_view, register_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',home, name="home_route"),
    path('login/', login_view, name="login"),
    path('register/', register_view, name="register"),
    path('dashboard/', include('dashboard.urls')),
    path('logout/', logout_view, name="logout")
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
