"""fantasy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from draft import views as draft_views
from users import views as users_views

urlpatterns = [
    path('', draft_views.index, name='index'),
    path('admin/', admin.site.urls),
    path('draft_board', draft_views.draft_board, name='draft_board'),
    path('draft_entry', draft_views.draft_entry, name='draft_entry'),
    path('value_dashboard', draft_views.value_dashboard, name='value_dashboard'),
    path('top_available', draft_views.top_available_players_board, name='top_available'),
    path('invalidate_data_frame', draft_views.invalidate_draft_frame, name='invalidate_data_frame'),
    path('replay', draft_views.replay, name='replay'),
    path('upload_projections/<int:draft_id>', draft_views.upload_projections, name='upload_projections'),
    path('create_draft', draft_views.create_draft, name='create_draft'),
    path('draft_configuration_home/<int:draft_id>', draft_views.draft_configuration_home, name='draft_configuration_home'),
    path('configure_projection_columns/<int:draft_id>', draft_views.configure_projection_columns, name='configure_projection_columns'),

    # Begin Users URLs
    path('register', users_views.register, name='register'),
    path('login', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('profile', users_views.profile, name='profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)