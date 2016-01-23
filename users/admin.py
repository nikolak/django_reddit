from django.contrib import admin

# Register your models here.
from reddit.admin import SubmissionInline
from users.models import RedditUser


class RedditUserAdmin(admin.ModelAdmin):
    inlines = [
        SubmissionInline,
    ]

admin.site.register(RedditUser, RedditUserAdmin)
