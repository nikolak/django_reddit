from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from reddit.forms import SubmissionForm
from reddit.models import RedditUser, Submission


class TestSubmissionForm(TestCase):
    def test_full_valid_submission(self):
        test_data = {
            'title': 'submission_title',
            'url': 'http://example.com',
            'text': 'submission text'
        }
        form = SubmissionForm(data=test_data)
        self.assertTrue(form.is_valid())

    def test_minimum_data_required(self):
        test_data = {
            'title': 'submission title'
        }
        form = SubmissionForm(data=test_data)
        self.assertTrue(form.is_valid())

    def test_invalid_data(self):
        test_data = {
            'title': '.' * 300,
            'url': 'notaurl',
            'text': '.' * 5001
        }
        form = SubmissionForm(data=test_data)
        self.assertEqual(form.errors['title'], [u"Ensure this value has at most 250 characters (it has 300)."])
        self.assertEqual(form.errors['url'], [u"Enter a valid URL."])
        self.assertEqual(form.errors['text'], [u"Ensure this value has at most 5000 characters (it has 5001)."])
        self.assertFalse(form.is_valid())


class TestSubmissionRequests(TestCase):
    def setUp(self):
        self.c = Client()
        self.login_data = {
            'username': 'submissiontest',
            'password': 'password'
        }
        RedditUser.objects.create(
            user=User.objects.create_user(**self.login_data)
        )

    def test_logged_out(self):
        r = self.c.get(reverse('Submit'))
        self.assertRedirects(r, "{}?next={}".format(
            reverse('Login'), reverse('Submit')
        ))

    def test_logged_in_GET(self):
        self.c.login(**self.login_data)
        r = self.c.get(reverse('Submit'))
        self.assertIsInstance(r.context['form'], SubmissionForm)

    def test_making_a_submission(self):
        self.c.login(**self.login_data)
        test_data = {
            'title': 'submission title',
            'url': 'http://example.com',
            'text': 'submission text'
        }
        r = self.c.post(reverse('Submit'), data=test_data, follow=True)
        submission = Submission.objects.filter(**test_data).first()
        self.assertIsNotNone(submission)
        self.assertRedirects(r, reverse('Thread', args=(submission.id,)))
        self.assertContains(r, 'Submission created')

    def test_missing_fields(self):
        self.c.login(**self.login_data)

        test_data = {
            'url': 'http://example.com',
            'text': 'submission text'
        }
        r = self.c.post(reverse('Submit'), data=test_data)
        self.assertNotContains(r, 'Submission created')
        self.assertContains(r, 'This field is required.')
