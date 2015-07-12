from django.test import TestCase
from reddit.forms import UserForm
from django.contrib.auth.models import User

class RegistrationFormTestCase(TestCase):

    def setUp(self):
        u = User(username = "user", password="password")
        u.save()

    def test_valid_form(self):
        test_data = {'username':'username',
                      'password':'password'}
        form = UserForm(data=test_data)
        self.assertTrue(form.is_valid())

    def test_invalid_username(self):
        test_data = {'username':'_',
                     'password':'password'}
        form = UserForm(data = test_data)
        self.assertEqual(form.errors['username'], [u"Ensure this value has at least 3 characters (it has 1)."])
        self.assertFalse(form.is_valid())

        test_data = {'username':'1234567890123',
                     'password':'password'}

        form = UserForm(data=test_data)
        self.assertEqual(form.errors['username'], [u"Ensure this value has at most 12 characters (it has 13)."])
        self.assertFalse(form.is_valid())

    def test_invalid_password(self):
        test_data = {'username':'username',
                     'password':'_'}
        form = UserForm(data = test_data)
        self.assertEqual(form.errors['password'], [u"Ensure this value has at least 4 characters (it has 1)."])
        self.assertFalse(form.is_valid())

    def test_existing_username(self):
        test_data ={'username':'user',
                    'password':'password'}

        form = UserForm(data=test_data)
        self.assertEqual(form.errors['username'], [u"A user with that username already exists."])
        self.assertFalse(form.is_valid())