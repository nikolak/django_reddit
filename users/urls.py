from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^register/$', views.register, name="register"),
    url(r'^login/$', views.user_login, name="login"),
    url(r'^logout/$', views.user_logout, name="logout"),
    url(r'^user/(?P<username>[0-9a-zA-Z_]*)$', views.user_profile, name="user_profile"),
    url(r'^profile/edit/$', views.edit_profile, name="edit_profile"),
]
