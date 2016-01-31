from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.contrib.auth.models import User


class Testlogout(TestCase):
    def setUp(self):
        self.c = Client()
        self.login_data = {'username': 'username',
                           'password': 'password'}
        User.objects.create_user(**self.login_data)

    def test_valid_logout(self):
        self.assertTrue(self.c.login(**self.login_data))
        r = self.c.post(reverse('logout'), follow=True)
        self.assertRedirects(r, reverse('frontpage'))
        self.assertContains(r, 'Logged out!')

    def test_custom_logout_redirect(self):
        self.assertTrue(self.c.login(**self.login_data))
        r = self.c.post(reverse('logout'), data={'current_page': reverse('login')}, follow=True)
        self.assertRedirects(r, reverse('login'))
        self.assertContains(r, 'Logged out!')

    def test_invalid_logout_request(self):
        r = self.c.post(reverse('logout'), follow=True)
        self.assertRedirects(r, reverse('frontpage'))
        self.assertTrue('Logged out!' not in r,
                        msg="User that was not logged in told he logged out successfully")
