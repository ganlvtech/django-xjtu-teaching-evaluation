from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^login/$', views.login),
    url(r'^logout/$', views.logout),
    url(r'^invalidate/$', views.invalidate),
    url(r'^$', views.index),
]
