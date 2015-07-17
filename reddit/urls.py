"""django_reddit URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
import views


urlpatterns = [
    url(r'^$', views.frontpage, name="Frontpage"),
    url(r'^comments/(?P<thread_id>[0-9]+)$', views.comments, name="Thread"),
    url(r'^login/$', views.user_login, name="Login"),
    url(r'^logout/$', views.user_logout, name="Logout"),
    url(r'^register/$', views.register, name="Register"),
    url(r'^submit/$', views.submit, name="Submit"),
    url(r'^user/(?P<username>\w+)$', views.user_profile, name="User Profile"),
    url(r'^profile/edit/$', views.edit_profile, name="Edit Profile"),

    url(r'^post/comment/$', views.post_comment, name="Post Comment"),
    url(r'^vote/$', views.vote, name="Vote on item"),


    url(r'^populate/$', views.test_data, name="Create test data"),

]
