from django.test import TestCase, Client
from reddit.forms import UserForm
from django.contrib.auth.models import User
from reddit.models import RedditUser


class RegistrationFormTestCase(TestCase):
    def setUp(self):
        User.objects.create(username="user", password="password")

    def test_valid_form(self):
        test_data = {'username': 'username',
                     'password': 'password'}
        form = UserForm(data=test_data)
        self.assertTrue(form.is_valid())

    def test_invalid_username(self):
        test_data = {'username': '_',
                     'password': 'password'}
        form = UserForm(data=test_data)
        self.assertEqual(form.errors['username'], [u"Ensure this value has at least 3 characters (it has 1)."])
        self.assertFalse(form.is_valid())

        test_data = {'username': '1234567890123',
                     'password': 'password'}

        form = UserForm(data=test_data)
        self.assertEqual(form.errors['username'], [u"Ensure this value has at most 12 characters (it has 13)."])
        self.assertFalse(form.is_valid())

    def test_invalid_password(self):
        test_data = {'username': 'username',
                     'password': '_'}
        form = UserForm(data=test_data)
        self.assertEqual(form.errors['password'], [u"Ensure this value has at least 4 characters (it has 1)."])
        self.assertFalse(form.is_valid())

    def test_existing_username(self):
        test_data = {'username': 'user',
                     'password': 'password'}

        form = UserForm(data=test_data)
        self.assertEqual(form.errors['username'], [u"A user with that username already exists."])
        self.assertFalse(form.is_valid())


class RegistrationPostTestCase(TestCase):
    def setUp(self):
        self.c = Client()

    def test_valid_data(self):
        test_data = {'username': 'username',
                     'password': 'password'}

        response = self.c.post('/register/', data=test_data)
        self.assertRedirects(response, '/login/')

        user = User.objects.filter(username=test_data['username']).first()
        self.assertIsNotNone(user,
                             msg="User account was not created, but form submission did not fail")

        redditUser = RedditUser.objects.filter(user=user).first()
        self.assertIsNotNone(redditUser,
                             msg="User created but not assigned to RedditUser model")

        self.assertTrue(self.c.login(**test_data), msg="User is unable to login.")

    def test_invalid_data(self):
        test_data = {'username': 'invalid_too_long_username',
                     'password': '_'}

        response = self.c.post('/register/', data=test_data)
        self.assertEqual(response.status_code, 200,
                         msg="Form submission failed, but a registration page was not returned again")
        self.assertIsNone(User.objects.filter(username=test_data['username']).first(),
                          msg="Invalid user instance created")
        self.assertFalse(self.c.login(**test_data), msg="Invalid user data can be used to login")
