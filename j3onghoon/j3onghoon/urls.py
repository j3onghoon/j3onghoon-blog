"""
URL configuration for j3onghoon project.

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
from django.urls import path, include
from blog import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", views.HomeView.as_view(), name="home"),
    path("posts/", views.PostListView.as_view(), name="posts"),
    path("posts/<int:pk>", views.PostDetailView.as_view(), name="post-detail"),
    path("guestbooks/", views.GuestBookListView.as_view(), name="guestbooks"),
    path("portfolios/", views.PortfolioListView.as_view(), name="portfolios"),
]
