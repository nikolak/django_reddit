import json
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from reddit.models import Submission, Comment, Vote
from users.models import RedditUser
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.http import HttpResponseNotAllowed, HttpResponseBadRequest


class TestViewingThreadComments(TestCase):
    def setUp(self):
        self.c = Client()
        self.credentials = {'username': 'username',
                            'password': 'password'}
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
        r = self.c.get(reverse('thread', args=(1,)))
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
        r = self.c.get(reverse('thread', args=(1,)))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['sub_vote'], 1)
        self.assertEqual(r.context['comment_votes'], {1: 1, 5: -1})
        self.assertContains(r, 'root comment', count=3)
        self.assertContains(r, 'reply comment', count=2)

    def test_invalid_thread_id(self):
        r = self.c.get(reverse('thread', args=(123,)))
        self.assertEqual(r.status_code, 404)


class TestPostingComment(TestCase):
    def setUp(self):
        self.c = Client()
        self.credentials = {'username': 'commentposttest',
                            'password': 'password'}
        author = RedditUser.objects.create(
            user=User.objects.create_user(**self.credentials)
        )

        Submission.objects.create(
            id=99,
            score=1,
            title=get_random_string(length=12),
            author=author
        )

    def test_post_only(self):
        r = self.c.get(reverse('post_comment'))
        self.assertIsInstance(r, HttpResponseNotAllowed)

    def test_logged_out(self):
        r = self.c.post(reverse('post_comment'))
        self.assertEqual(r.status_code, 200)
        json_response = json.loads(r.content.decode("utf-8"))
        self.assertEqual(json_response['msg'], "You need to log in to post new comments.")

    def test_missing_type_or_id(self):
        self.c.login(**self.credentials)
        for key in ['parentType', 'parentId']:
            r = self.c.post(reverse('post_comment'),
                            data={key: 'comment'})
            self.assertIsInstance(r, HttpResponseBadRequest)
        r = self.c.post(reverse('post_comment'),
                        data={'parentType': 'InvalidType',
                              'parentId': 1})
        self.assertIsInstance(r, HttpResponseBadRequest)

    def test_no_comment_text(self):
        self.c.login(**self.credentials)
        test_data = {
            'parentType': 'submission',
            'parentId': 1,
            'commentContent': ''
        }
        r = self.c.post(reverse('post_comment'), data=test_data)
        self.assertEqual(r.status_code, 200)
        json_response = json.loads(r.content.decode("utf-8"))
        self.assertEqual(json_response['msg'],
                         'You have to write something.')

    def test_invalid_or_wrong_parent_id(self):
        self.c.login(**self.credentials)
        test_data = {
            'parentType': 'submission',
            'parentId': 'invalid',
            'commentContent': 'content'
        }
        r = self.c.post(reverse('post_comment'), data=test_data)
        self.assertIsInstance(r, HttpResponseBadRequest)

        test_data = {
            'parentType': 'submission',
            'parentId': 9999,
            'commentContent': 'content'
        }

        r = self.c.post(reverse('post_comment'), data=test_data)
        self.assertIsInstance(r, HttpResponseBadRequest)

        test_data = {
            'parentType': 'comment',
            'parentId': 9999,
            'commentContent': 'content'
        }

        r = self.c.post(reverse('post_comment'), data=test_data)
        self.assertIsInstance(r, HttpResponseBadRequest)

    def test_valid_comment_posting_thread(self):
        self.c.login(**self.credentials)
        test_data = {
            'parentType': 'submission',
            'parentId': 99,
            'commentContent': 'thread root comment'
        }

        r = self.c.post(reverse('post_comment'), data=test_data)
        self.assertEqual(r.status_code, 200)
        json_r = json.loads(r.content.decode("utf-8"))
        self.assertEqual(json_r['msg'], 'Your comment has been posted.')
        all_comments = Comment.objects.filter(
            submission=Submission.objects.get(id=99)
        )
        self.assertEqual(all_comments.count(), 1)
        comment = all_comments.first()
        self.assertEqual(comment.html_comment, '<p>thread root comment</p>\n')
        self.assertEqual(comment.author.user.username, self.credentials['username'])

    def test_valid_comment_posting_reply(self):
        self.c.login(**self.credentials)
        thread = Submission.objects.get(id=99)
        author = RedditUser.objects.get(user=User.objects.get(
            username=self.credentials['username']
        ))
        comment = Comment.create(author, 'root comment', thread)
        comment.save()
        self.assertEqual(Comment.objects.filter(submission=thread).count(), 1)

        test_data = {
            'parentType': 'comment',
            'parentId': comment.id,
            'commentContent': 'thread reply comment'
        }

        r = self.c.post(reverse('post_comment'), data=test_data)
        self.assertEqual(r.status_code, 200)
        json_r = json.loads(r.content.decode("utf-8"))
        self.assertEqual(json_r['msg'], 'Your comment has been posted.')
        self.assertEqual(Comment.objects.filter(submission=thread).count(), 2)

        comment = Comment.objects.filter(submission=thread,
                                         id=2).first()
        self.assertEqual(comment.html_comment, '<p>thread reply comment</p>\n')
