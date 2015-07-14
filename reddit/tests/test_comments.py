from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from reddit.models import RedditUser, Submission, Comment, Vote
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string


class TestViewingThreadComments(TestCase):
    def setUp(self):
        self.c = Client()
        self.credentials = {'username':'username',
                            'password':'password'}
        author = RedditUser.objects.create(
            user=User.objects.create_user(**self.credentials)
        )

        submission = Submission.objects.create(
            id=1,
            score=1,
            title=get_random_string(length=12),
            author=author
        )

        for _ in range(3):
            Comment.objects.create(
                author_name=author.user.username,
                author=author,
                submission=submission,
                html_comment="root comment"
            )

        # Add some replies
        parent = Comment.objects.get(id=1)
        for _ in range(2):
            Comment.objects.create(
                author_name=author.user.username,
                author=author,
                submission=submission,
                parent=parent,
                html_comment="reply comment"
            )

        # add upvote to one root comment,
        Vote.create(
            user=author,
            vote_object=Comment.objects.get(id=1),
            vote_value=1
        ).save()

        # and downvote to one reply comment
        Vote.create(
            user=author,
            vote_object=Comment.objects.get(id=5),
            vote_value=-1
        ).save()

        # add upvote to the submission
        Vote.create(
            user=author,
            vote_object=submission,
            vote_value=1
        ).save()

    def test_valid_public_comment_view(self):
        self.c.logout()
        r = self.c.get(reverse('Thread', args=(1,)))
        submission = Submission.objects.get(id=1)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['submission'], submission)
        self.assertEqual(len(r.context['comments']), 5)
        self.assertContains(r, 'root comment', count=3)
        self.assertContains(r, 'reply comment', count=2)
        self.assertEqual(r.context['comment_votes'], {})
        self.assertIsNone(r.context['sub_vote'])

    def test_comment_votes(self):
        self.c.login(**self.credentials)
        r = self.c.get(reverse('Thread', args=(1,)))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['sub_vote'], 1)
        self.assertEqual(r.context['comment_votes'], {1:1, 5:-1})
        self.assertContains(r, 'root comment', count=3)
        self.assertContains(r, 'reply comment', count=2)

    def test_invalid_thread_id(self):
        r = self.c.get(reverse('Thread', args=(123,)))
        self.assertEqual(r.status_code, 404)