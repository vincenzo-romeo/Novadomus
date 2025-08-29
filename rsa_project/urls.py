from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),                 # home & dashboard
    path('login/',  auth_views.LoginView.as_view(), name='login'),
    path('loggedout/', LogoutView.as_view(), name='logout'),
]
