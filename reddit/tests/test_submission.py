from django.test import TestCase, Client
from reddit.forms import SubmissionForm


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
