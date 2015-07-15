from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.contrib.auth.models import User
from reddit.models import RedditUser


class TestProfileViewing(TestCase):
    def setUp(self):
        self.c = Client()
        r = RedditUser.objects.create(
            user=User.objects.create_user(
                username="username",
                password="password"
            )
        )

        r.first_name = "First Name"
        r.last_name = "Last Name"
        r.about_html = "about html text"
        r.github = "example"

    def test_existing_username(self):
        r = self.c.get(reverse('User Profile', args=('username',)))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '(username)')
        self.assertContains(r, 'compose?to=username')
        self.assertNotContains(r, '/profile/edit')
        self.assertNotContains(r, 'First Name')
        self.assertNotContains(r, 'Last Name')
        self.assertNotContains(r, 'about html text')
        self.assertNotContains(r, 'https://github.com/example')

    def test_own_username(self):
        self.assertTrue(self.c.login(username='username', password='password'))
        r = self.c.get(reverse('User Profile', args=('username',)))
        self.assertContains(r, '/profile/edit')
        self.assertNotContains(r, 'compose?to=username')
        self.c.logout()

    def test_invalid_username(self):
        r = self.c.get(reverse('User Profile', args=('none',)))
        self.assertEqual(r.status_code, 404)
