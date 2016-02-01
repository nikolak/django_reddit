from django.contrib.contenttypes.models import ContentType
from mptt.models import MPTTModel
from django.db import models


class ContentTypeAware(models.Model):
    def get_content_type(self):
        """:return: Content type for this instance."""
        return ContentType.objects.get_for_model(self)

    def get_content_type_id(self):
        """:return: Content type ID for this instance"""
        return self.get_content_type().pk

    def add_vote(self, vote_value):
        self.score += vote_value
        if vote_value == 1:
            self.ups += 1
        elif vote_value == -1:
            self.downs += 1

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
