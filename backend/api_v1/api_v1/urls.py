"""
URL configuration for api_v1 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
import os
from api1 import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    # path("admin/", admin.site.urls),
    path("api/v1/auth/register", views.RegistrationView.as_view()),
    path("api/v1/auth/login", views.LoginView.as_view()),
    path("api/v1/auth/me", views.UserView.get_current_user),
    path("api/v1/auth/refresh", TokenRefreshView.as_view(), name="refresh_token"),
    path("api/v1/jobs", views.PostsView.as_view()),
    path("api/v1/jobs/create", views.CreatePostView.as_view()),
    path("api/v1/jobs/<int:id>", views.PostView.as_view()),
]
