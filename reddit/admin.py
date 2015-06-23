from django.contrib import admin
from reddit.models import RedditUser,Submission,Comment,Vote

# Register your models here.
class SubmissionInline(admin.TabularInline):
    model = Submission
    max_num = 10

class CommentsInline(admin.StackedInline):
    model = Comment
    max_num = 10

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'author')
    inlines = [CommentsInline]

class RedditUserAdmin(admin.ModelAdmin):
    inlines = [
        SubmissionInline,
    ]

admin.site.register(RedditUser, RedditUserAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Comment)
admin.site.register(Vote)