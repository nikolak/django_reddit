from hashlib import md5

import mistune
from django.contrib.auth.models import User
from django.db import models


class RedditUser(models.Model):
    user = models.OneToOneField(User)
    first_name = models.CharField(max_length=35, null=True, default=None,
                                  blank=True)
    last_name = models.CharField(max_length=35, null=True, default=None,
                                 blank=True)
    email = models.EmailField(null=True, blank=True, default=None)
    about_text = models.TextField(blank=True, null=True, max_length=500,
                                  default=None)
    about_html = models.TextField(blank=True, null=True, default=None)
    gravatar_hash = models.CharField(max_length=32, null=True, blank=True,
                                     default=None)
    display_picture = models.NullBooleanField(default=False)
    homepage = models.URLField(null=True, blank=True, default=None)
    twitter = models.CharField(null=True, blank=True, max_length=15,
                               default=None)
    github = models.CharField(null=True, blank=True, max_length=39,
                              default=None)

    comment_karma = models.IntegerField(default=0)
    link_karma = models.IntegerField(default=0)

    def update_profile_data(self):
        self.about_html = mistune.markdown(self.about_text)
        if self.display_picture:
            self.gravatar_hash = md5(self.email.lower().encode('utf-8')).hexdigest()

    def __unicode__(self):
        return "<RedditUser:{}>".format(self.user.username)
