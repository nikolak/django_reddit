from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.contrib.auth.models import User


class TestloginPOST(TestCase):
    def setUp(self):
        self.c = Client()
        self.valid_data = {"username": "user",
                           "password": "password"}
        self.invalid_data = {"username": "none",
                             "password": "none"}
        User.objects.create_user(**self.valid_data)

    def test_valid_login(self):
        r = self.c.post(reverse('login'), data=self.valid_data, follow=True)
        self.assertRedirects(r, reverse('frontpage'))
        self.assertTrue(self.c.login(**self.valid_data))

    def test_invalid_login(self):
        r = self.c.post(reverse('login'), data=self.invalid_data)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Wrong username or password.")
        self.assertFalse(self.c.login(**self.invalid_data))

    def test_disabled_account(self):
        u = User.objects.get(username=self.valid_data['username'])
        u.is_active = False
        u.save()
        r = self.c.post(reverse('login'), data=self.valid_data)
        self.assertContains(r, "Account disabled", status_code=200)

    def test_already_logged_in(self):
        self.c.post(reverse('login'), data=self.valid_data)
        r = self.c.post(reverse('login'), data=self.valid_data)
        self.assertContains(r, 'You are already logged in.')

    def test_login_redirect(self):
        redirect_data = {'username': self.valid_data['username'],
                         'password': self.valid_data['password'],
                         'next': reverse('submit')}
        r = self.c.post(reverse('login'), data=redirect_data)
        self.assertRedirects(r, reverse('submit'))

    def test_malformed_request(self):
        r = self.c.post(reverse('login'), data={"a": "a", 1: "b"})
        self.assertEqual(r.status_code, 400)
