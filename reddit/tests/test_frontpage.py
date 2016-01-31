from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from reddit.models import Submission, Vote
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from users.models import RedditUser

class TestFrontPageGET(TestCase):
    def setUp(self):
        self.c = Client()
        author = RedditUser.objects.create(
            user=User.objects.create_user(username="username",
                                          password="password"))

        for i in range(50):
            Submission.objects.create(score=i ** 2,
                                      title=get_random_string(length=20),
                                      author=author)

    def test_submission_count(self):
        self.assertEqual(Submission.objects.all().count(), 50)

    def test_no_page_number(self):
        r = self.c.get(reverse('frontpage'))
        self.assertEqual(len(r.context['submissions']), 25)
        self.assertEqual(r.context['submissions'].number, 1)
        self.assertFalse(r.context['submissions'].has_previous())
        self.assertTrue(r.context['submissions'].has_next())

    def test_valid_page_number(self):
        r = self.c.get(reverse('frontpage'), data={'page': 1})
        self.assertEqual(len(r.context['submissions']), 25)
        first_page_submissions = r.context['submissions']
        self.assertFalse(r.context['submissions'].has_previous())

        r = self.c.get(reverse('frontpage'), data={'page': 2})
        self.assertEqual(len(r.context['submissions']), 25)
        second_page_submissions = r.context['submissions']
        self.assertNotEqual(first_page_submissions, second_page_submissions)

        self.assertFalse(r.context['submissions'].has_next())

    def test_invalid_page_number(self):
        r = self.c.get(reverse('frontpage'), data={'page': "something"}, follow=True)
        self.assertEqual(r.status_code, 404)

    def test_wrong_page_number(self):
        r = self.c.get(reverse('frontpage'), data={'page': 10}, follow=True)
        self.assertEqual(r.context['submissions'].number, 2)
        self.assertFalse(r.context['submissions'].has_next())

        self.assertTrue(r.context['submissions'].has_previous())
        self.assertEqual(r.context['submissions'].previous_page_number(), 1)


class TestFrontpageVotes(TestCase):
    def setUp(self):
        self.c = Client()
        author = RedditUser.objects.create(
            user=User.objects.create_user(username="username",
                                          password="password"))

        for i in range(50):
            Submission.objects.create(score=50 - i,
                                      title=get_random_string(length=20),
                                      author=author).save()

        for i in range(1, 50, 10):
            # [1, 11, 21] [31, 41] have upvotes (lists demonstrate pages)
            Vote.create(user=author,
                        vote_object=Submission.objects.get(id=i),
                        vote_value=1).save()

        for i in range(2, 50, 15):
            # [2, 17] [32, 47] have downvotes (lists demonstrate pages)
            Vote.create(user=author,
                        vote_object=Submission.objects.get(id=i),
                        vote_value=-1).save()

    def test_logged_out(self):
        r = self.c.get(reverse('frontpage'))
        self.assertEqual(r.context['submission_votes'], {},
                         msg="Logged out user got some submission votes data")

    def test_logged_in(self):
        self.c.login(username='username', password='password')
        r = self.c.get(reverse('frontpage'))
        self.assertEqual(len(r.context['submission_votes']), 5)

        upvote_keys = []
        downvote_keys = []
        for post_id, vote_value in list(r.context['submission_votes'].items()):
            if vote_value == 1:
                upvote_keys.append(post_id)
            elif vote_value == -1:
                downvote_keys.append(post_id)

        self.assertEqual(upvote_keys, [1, 11, 21],
                         msg="Got wrong values for submission upvotes")
        self.assertEqual(downvote_keys, [2, 17],
                         msg="Got wrong values for submission downvotes")

    def test_second_page(self):
        self.c.login(username='username', password='password')
        r = self.c.get(reverse('frontpage'), data={'page': 2})
        self.assertEqual(len(r.context['submission_votes']), 4)

        upvote_keys = []
        downvote_keys = []
        for post_id, vote_value in list(r.context['submission_votes'].items()):
            if vote_value == 1:
                upvote_keys.append(post_id)
            elif vote_value == -1:
                downvote_keys.append(post_id)

        self.assertEqual(upvote_keys, [41, 31])
        self.assertEqual(downvote_keys, [32, 47],
                         msg="Got wrong values for submission downvotes")
