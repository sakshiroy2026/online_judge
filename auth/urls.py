"""
URL configuration for auth project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path,include
from sign_up.views import home
from problem_detail.views import submit
from sign_up.views import login_user
from dashboard.views import dashboard

urlpatterns = [
    path('', home, name='home'),

    path('dashboard/problem/<int:id>', submit, name='submit'),
    path('compile/', include('compile.urls')),
    path('dashboard/', include('dashboard.urls')),
    path("admin/", admin.site.urls),
    path('auth/', include('sign_up.urls')),
    path('question/<int:id>/', include('problem_detail.urls')),
    path('auth/login/', login_user, name='login'),
    path('auth/login/dashboard/', dashboard, name='login'),
    
]
# Serve media files during development/
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)