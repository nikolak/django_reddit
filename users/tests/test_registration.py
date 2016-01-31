from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from reddit.forms import UserForm
from django.contrib.auth.models import User
from users.models import RedditUser


class RegistrationFormTestCase(TestCase):
    def setUp(self):
        User.objects.create(username="user", password="password")

    def test_valid_form(self):
        test_data = {'username': 'username',
                     'password': 'password'}
        form = UserForm(data=test_data)
        self.assertTrue(form.is_valid())

    def test_too_short_username(self):
        test_data = {'username': '_',
                     'password': 'password'}
        form = UserForm(data=test_data)
        self.assertEqual(form.errors['username'], [
            "Ensure this value has at least 3 characters (it has 1)."])
        self.assertFalse(form.is_valid())

    def test_too_long_username(self):
        test_data = {'username': '1234567890123',
                     'password': 'password'}

        form = UserForm(data=test_data)
        self.assertEqual(form.errors['username'], [
            "Ensure this value has at most 12 characters (it has 13)."])
        self.assertFalse(form.is_valid())

    def test_invalid_username(self):
        test_data = {'username': 'matt-ex',
                     'password': 'password'}
        form = UserForm(data=test_data)
        self.assertEqual(form.errors['username'],
                         ["This value may contain only letters, "
                          "numbers and _ characters."])

    def test_invalid_password(self):
        test_data = {'username': 'username',
                     'password': '_'}
        form = UserForm(data=test_data)
        self.assertEqual(form.errors['password'], [
            "Ensure this value has at least 4 characters (it has 1)."])
        self.assertFalse(form.is_valid())

    def test_existing_username(self):
        test_data = {'username': 'user',
                     'password': 'password'}

        form = UserForm(data=test_data)
        self.assertEqual(form.errors['username'],
                         ["A user with that username already exists."])
        self.assertFalse(form.is_valid())

    def test_missing_username(self):
        test_data = {'password': 'password'}
        form = UserForm(data=test_data)
        self.assertEqual(form.errors['username'], ["This field is required."])

    def test_missing_password(self):
        test_data = {'username': 'username'}
        form = UserForm(data=test_data)
        self.assertEqual(form.errors['password'], ["This field is required."])


class RegistrationPostTestCase(TestCase):
    def setUp(self):
        self.c = Client()

    def test_logged_in(self):
        User.objects.create_user(username='regtest', password='password')
        self.c.login(username='regtest', password='password')
        r = self.c.get(reverse('register'))
        self.assertContains(r, 'You are already registered and logged in.')
        self.assertContains(r, 'type="submit" disabled')

    def test_valid_data(self):
        test_data = {'username': 'username',
                     'password': 'password'}

        response = self.c.post(reverse('register'), data=test_data)
        self.assertRedirects(response, reverse('frontpage'))

        user = User.objects.filter(username=test_data['username']).first()
        self.assertIsNotNone(user,
                             msg="User account was not created, but form submission did not fail")

        redditUser = RedditUser.objects.filter(user=user).first()
        self.assertIsNotNone(redditUser,
                             msg="User created but not assigned to RedditUser model")

        self.assertTrue(self.c.login(**test_data),
                        msg="User is unable to login.")
        self.assertEqual(RedditUser.objects.all().count(), 1)
        self.assertEqual(User.objects.all().count(), 1)

    def test_invalid_data(self):
        test_data = {'username': 'invalid_too_long_username',
                     'password': '_'}

        response = self.c.post(reverse('register'), data=test_data)
        self.assertEqual(response.status_code, 200,
                         msg="Form submission failed, but a registration page was not returned again")
        self.assertIsNone(
            User.objects.filter(username=test_data['username']).first(),
            msg="Invalid user instance created")
        self.assertFalse(self.c.login(**test_data),
                         msg="Invalid user data can be used to login")

    def test_malformed_post_request(self):
        response = self.c.post(reverse('register'), data={'a': "a", 1: "b"})
        self.assertContains(response, 'This field is required.', count=2)
