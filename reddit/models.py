from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from mptt.models import MPTTModel, TreeForeignKey
from hashlib import md5
import mistune


class ContentTypeAware(models.Model):
    def get_content_type(self):
        """:return: Content type for this instance."""
        return ContentType.objects.get_for_model(self)

    def get_content_type_id(self):
        """:return: Content type ID for this instance"""
        return self.get_content_type().pk

    class Meta:
        abstract = True


class MttpContentTypeAware(MPTTModel):
    def get_content_type(self):
        """:return: Content type for this instance."""
        return ContentType.objects.get_for_model(self)

    def get_content_type_id(self):
        """:return: Content type ID for this instance"""
        return self.get_content_type().pk

    class Meta:
        abstract = True


class RedditUser(models.Model):
    user = models.OneToOneField(User)
    first_name = models.CharField(max_length=35,null=True, default=None, blank=True)
    last_name = models.CharField(max_length=35, null=True, default=None, blank=True)
    email = models.EmailField(null=True, blank=True, default=None)
    about_text = models.TextField(blank=True,null=True, max_length=500, default=None)
    about_html = models.TextField(blank=True,null=True,default=None)
    gravatar_hash = models.CharField(max_length=32,null=True,blank=True, default=None)
    display_picture = models.NullBooleanField(default=False)
    homepage = models.URLField(null=True, blank=True, default=None)
    twitter = models.CharField(null=True,blank=True, max_length=15, default=None)
    github = models.CharField(null=True, max_length=39, default=None)

    comment_karma = models.IntegerField(default=0)
    link_karma = models.IntegerField(default=0)

    def update_profile_data(self):
        self.about_html=mistune.markdown(self.about_text)
        if self.display_picture:
            self.gravatar_hash = md5(self.email.lower()).hexdigest()

    def __unicode__(self):
        return "<RedditUser:{}>".format(self.user.username)


class Submission(ContentTypeAware):
    author = models.ForeignKey(RedditUser)
    title = models.CharField(max_length=250)
    url = models.URLField(null=True, blank=True)
    text = models.TextField(max_length=5000, blank=True)
    ups = models.IntegerField(default=0)
    downs = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)
    comment_count = models.IntegerField(default=0)

    @property
    def author_name(self):
        return self.author.user.username

    @property
    def linked_url(self):
        if self.url:
            return "{}".format(self.url)
        else:
            return "/comments/{}".format(self.id)

    @property
    def comments_url(self):
        return '/comments/{}'.format(self.id)

    def __unicode__(self):
        return "<Submission:{}>".format(self.id)


class Comment(MttpContentTypeAware):
    author = models.CharField(null=False, max_length=12)
    submission = models.ForeignKey(Submission)
    parent = TreeForeignKey('self', related_name='children', null=True, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now)
    ups = models.IntegerField(default=0)
    downs = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    raw_comment = models.TextField(blank=True)
    html_comment = models.TextField(blank=True)

    class MPTTMeta:
        order_insertion_by = ['-score']

    @classmethod
    def create(cls, author, raw_comment, parent):
        """
        Create a new comment instance. If the parent is submisison
        update comment_count field and save it.
        If parent is comment post it as child comment
        :param author: RedditUser instance
        :type author: RedditUser
        :param raw_comment: Raw comment text
        :type raw_comment: str
        :param parent: Comment or Submission that this comment is child of
        :type parent: Comment | Submission
        :return: New Comment instance
        :rtype: Comment
        """

        html_comment = mistune.markdown(raw_comment)  # todo: any exceptions possible?
        comment = cls(author=author.user.username,
                      raw_comment=raw_comment,
                      html_comment=html_comment)

        if isinstance(parent, Submission):
            submission = parent
            comment.submission = submission
        elif isinstance(parent, Comment):
            submission = parent.submission
            comment.submission = submission
            comment.parent = parent
        else:
            return
        submission.comment_count += 1
        submission.save()

        return comment

    def __unicode__(self):
        return "<Comment:{}>".format(self.id)


class Vote(models.Model):
    user = models.ForeignKey(RedditUser)
    submission = models.ForeignKey(Submission)
    vote_object_type = models.ForeignKey(ContentType)
    vote_object_id = models.PositiveIntegerField()
    vote_object = GenericForeignKey('vote_object_type', 'vote_object_id')
    value = models.IntegerField(default=0)

    @classmethod
    def create(cls, user, vote_object, vote_value):
        """
        Create a new vote object and return it.
        It will also update the ups/downs/score fields in the
        vote_object instance and save it.

        :param user: RedditUser instance
        :type user: RedditUser
        :param vote_object: Instance of the object the vote is cast on
        :type vote_object: Comment | Submission
        :param vote_value: Value of the vote
        :type vote_value: int
        :return: new Vote instance
        :rtype: Vote
        """

        if isinstance(vote_object, Submission):
            submission = vote_object
        else:
            submission = vote_object.submission

        vote = cls(user=user,
                   vote_object=vote_object,
                   value=vote_value)

        vote.submission = submission
        # the value for new vote will never be 0
        # that can happen only when removing up/down vote.
        vote_object.score += vote_value
        if vote_value == 1:
            vote_object.ups += 1
        elif vote_value == -1:
            vote_object.downs += 1

        vote_object.save()

        return vote
