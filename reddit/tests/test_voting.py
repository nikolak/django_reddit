import json
from django.core.urlresolvers import reverse
from django.http import HttpResponseNotAllowed, HttpResponseForbidden, \
    HttpResponseBadRequest
from django.test import Client, TestCase
from reddit.models import Comment, Submission, Vote
from django.contrib.auth.models import User
from users.models import RedditUser

class TestVotingOnItems(TestCase):
    def setUp(self):
        self.c = Client()
        self.credentials = {
            'username': 'voteusername',
            'password': 'password'
        }

        author = RedditUser.objects.create(
            user=User.objects.create_user(
                **self.credentials
            )
        )

        submission = Submission.objects.create(
            author=author,
            author_name=author.user.username,
            title="vote testing"
        )

        Comment.create(author=author,
                       raw_comment="root comment",
                       parent=submission).save()

    def test_post_only(self):
        r = self.c.get(reverse('vote'))
        self.assertIsInstance(r, HttpResponseNotAllowed)

    def test_logged_out(self):
        test_data = {
            'what': 'submission',
            'what_id': 1,
            'vote_value': 1
        }

        r = self.c.post(reverse('vote'), data=test_data)
        self.assertIsInstance(r, HttpResponseForbidden)

    def test_invalid_vote_value(self):
        self.c.login(**self.credentials)
        test_data = {
            'what': 'submission',
            'what_id': 1,
            'vote_value': '2'
        }
        r = self.c.post(reverse('vote'), data=test_data)
        self.assertIsInstance(r, HttpResponseBadRequest)

    def test_missing_arugmnets(self):
        self.c.login(**self.credentials)
        r = self.c.post(reverse('vote'),
                        data={
                            'what': 'submission',
                            'what_id': 1
                        })
        self.assertIsInstance(r, HttpResponseBadRequest)
        r = self.c.post(reverse('vote'),
                        data={
                            'what': 'submission',
                            'vote_value': '1'
                        })
        self.assertIsInstance(r, HttpResponseBadRequest)
        r = self.c.post(reverse('vote'),
                        data={
                            'what_id': '1',
                            'vote_value': '1'
                        })
        self.assertIsInstance(r, HttpResponseBadRequest)
        r = self.c.post(reverse('vote'), data={})
        self.assertIsInstance(r, HttpResponseBadRequest)

    def test_invalid_vote_object_id(self):
        self.c.login(**self.credentials)
        for what_type in ['comment', 'submission']:
            test_data = {
                'what': what_type,
                'what_id': 9999,
                'what_value': '1'
            }
            r = self.c.post(reverse('vote'), data=test_data)
            self.assertIsInstance(r, HttpResponseBadRequest)

    def test_submission_first_vote(self):
        submission = Submission.objects.filter(title="vote testing").first()
        self.assertIsNotNone(submission)
        self.c.login(**self.credentials)
        r = self.c.post(reverse('vote'),
                        data={
                            'what': 'submission',
                            'what_id': submission.id,
                            'vote_value': '1'
                        })
        self.assertEqual(r.status_code, 200)
        json_r = json.loads(r.content.decode("utf-8"))
        self.assertIsNone(json_r['error'])
        self.assertEqual(json_r['voteDiff'], 1)
        submission = Submission.objects.filter(title="vote testing").first()
        self.assertEqual(submission.score, 1)

    def test_submission_vote_cancel_or_reverse(self):
        submission = Submission.objects.filter(title="vote testing").first()
        user = RedditUser.objects.get(
            user=User.objects.get(username=self.credentials['username']))
        self.assertIsNotNone(submission)
        self.assertIsNotNone(user)
        Vote.create(user=user, vote_object=submission, vote_value=1).save()

        self.c.login(**self.credentials)
        r = self.c.post(reverse('vote'),
                        data={
                            'what': 'submission',
                            'what_id': submission.id,
                            'vote_value': '1'
                        })
        self.assertEqual(r.status_code, 200)
        json_r = json.loads(r.content.decode("utf-8"))
        self.assertIsNone(json_r['error'])
        self.assertEqual(json_r['voteDiff'], -1)

        vote = Vote.objects.get(vote_object_type=submission.get_content_type(),
                                vote_object_id=submission.id,
                                user=user)
        vote.value = 1
        vote.save()

        self.c.login(**self.credentials)
        r = self.c.post(reverse('vote'),
                        data={
                            'what': 'submission',
                            'what_id': submission.id,
                            'vote_value': '-1'
                        })
        self.assertEqual(r.status_code, 200)
        json_r = json.loads(r.content.decode("utf-8"))
        self.assertIsNone(json_r['error'])
        self.assertEqual(json_r['voteDiff'], -2)

    def test_comment_first_vote(self):
        submission = Submission.objects.filter(title="vote testing").first()
        self.assertIsNotNone(submission)
        comment = Comment.objects.filter(submission=submission).first()
        self.assertIsNotNone(comment)
        self.c.login(**self.credentials)
        r = self.c.post(reverse('vote'),
                        data={
                            'what': 'comment',
                            'what_id': comment.id,
                            'vote_value': '1'
                        })
        self.assertEqual(r.status_code, 200)
        json_r = json.loads(r.content.decode("utf-8"))
        self.assertIsNone(json_r['error'])
        self.assertEqual(json_r['voteDiff'], 1)
        scomment = Comment.objects.filter(submission=submission).first()
        self.assertEqual(scomment.score, 1)

    def test_comment_vote_cancel_or_reverse(self):
        submission = Submission.objects.filter(title="vote testing").first()
        user = RedditUser.objects.get(
            user=User.objects.get(username=self.credentials['username']))
        self.assertIsNotNone(submission)
        self.assertIsNotNone(user)
        comment = Comment.objects.filter(submission=submission).first()
        self.assertIsNotNone(comment)
        Vote.create(user=user, vote_object=comment, vote_value=1).save()

        self.c.login(**self.credentials)
        r = self.c.post(reverse('vote'),
                        data={
                            'what': 'comment',
                            'what_id': comment.id,
                            'vote_value': '1'
                        })
        self.assertEqual(r.status_code, 200)
        json_r = json.loads(r.content.decode("utf-8"))
        self.assertIsNone(json_r['error'])
        self.assertEqual(json_r['voteDiff'], -1)

        vote = Vote.objects.get(vote_object_type=comment.get_content_type(),
                                vote_object_id=comment.id,
                                user=user)
        vote.value = 1
        vote.save()

        self.c.login(**self.credentials)
        r = self.c.post(reverse('vote'),
                        data={
                            'what': 'comment',
                            'what_id': comment.id,
                            'vote_value': '-1'
                        })
        self.assertEqual(r.status_code, 200)
        json_r = json.loads(r.content.decode("utf-8"))
        self.assertIsNone(json_r['error'])
        self.assertEqual(json_r['voteDiff'], -2)
