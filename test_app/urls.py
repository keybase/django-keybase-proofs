from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

from .views import LoginView
from .views import LogoutView

urlpatterns = [
    url(r'^$',
        TemplateView.as_view(template_name='index.html'), name='index'),

    url(r'^accounts/login/(?P<username>.+)?', LoginView.as_view(), name='auth_login'),
    url(r'^accounts/logout/?', LogoutView.as_view(), name='auth_logout'),

    url(r'^keybase-proofs/',
        include('keybase_proofs.urls', namespace="keybase_proofs")),
]
