from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.contrib.auth.models import User
from users.models import RedditUser
from reddit.forms import ProfileForm


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
        r = self.c.get(reverse('user_profile', args=('username',)))
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
        r = self.c.get(reverse('user_profile', args=('username',)))
        self.assertContains(r, '/profile/edit')
        self.assertNotContains(r, 'compose?to=username')
        self.c.logout()

    def test_invalid_username(self):
        r = self.c.get(reverse('user_profile', args=('none',)))
        self.assertEqual(r.status_code, 404)


class TestProfileEditingForm(TestCase):
    def setUp(self):
        self.valid_data = {
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email@example.com',
            'display_picture': False,
            'about_text': 'about_text',
            'homepage': 'http://example.com',
            'github': 'username',
            'twitter': 'username',
        }

        self.invalid_data = {
            'first_name': 'too_long_first_name',
            'last_name': 'too_long_last_name',
            'email': 'notanemail',
            'display_picture': False,
            'about_text': 'toolong' * 75,
            'homepage': 'notadomain',
            'github': 'toolong' * 10,
            'twitter': 'toolong' * 5,
        }

    def test_all_valid_data(self):
        form = ProfileForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_invalid_data(self):
        form = ProfileForm(data=self.invalid_data)
        self.assertEqual(form.errors['first_name'], ["Ensure this value has at most 12 characters (it has 19)."])
        self.assertEqual(form.errors['last_name'], ["Ensure this value has at most 12 characters (it has 18)."])
        self.assertEqual(form.errors['email'], ["Enter a valid email address."])
        self.assertEqual(form.errors['about_text'], ["Ensure this value has at most 500 characters (it has 525)."])
        self.assertEqual(form.errors['homepage'], ["Enter a valid URL."])
        self.assertEqual(form.errors['github'], ["Ensure this value has at most 39 characters (it has 70)."])
        self.assertEqual(form.errors['twitter'], ["Ensure this value has at most 15 characters (it has 35)."])
        self.assertFalse(form.is_valid())

    def test_empty_data(self):
        test_data = {
            'first_name': '',
            'last_name': '',
            'email': '',
            'display_picture': False,
            'about_text': '',
            'homepage': '',
            'github': '',
            'twitter': '',
        }
        form = ProfileForm(data=test_data)
        self.assertTrue(form.is_valid())


class TestProfilePageRequests(TestCase):
    def setUp(self):
        self.c = Client()
        RedditUser.objects.create(
            user=User.objects.create_user(username='profiletest',
                                          password='password')
        )
        self.valid_data = {
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email@example.com',
            'display_picture': True,
            'about_text': 'about_text',
            'homepage': 'http://example.com',
            'github': 'username',
            'twitter': 'username',
        }

    def test_not_logged_in(self):
        r = self.c.get(reverse('edit_profile'))
        self.assertRedirects(r, reverse('login') + '?next=' + reverse('edit_profile'))

    def test_invalid_request(self):
        self.c.login(username='profiletest',
                     password='password')
        r = self.c.delete(reverse('edit_profile'))
        self.assertEqual(r.status_code, 404)

    def test_form_view(self):
        self.c.login(username='profiletest',
                     password='password')
        r = self.c.get(reverse('edit_profile'))
        self.assertIsInstance(r.context['form'], ProfileForm)

    def test_form_submit(self):
        self.c.login(username='profiletest',
                     password='password')

        r = self.c.post(reverse('edit_profile'), data=self.valid_data)
        self.assertEqual(r.status_code, 200)

        user = RedditUser.objects.get(user=User.objects.get(
            username='profiletest'
        ))
        for name, value in list(self.valid_data.items()):
            self.assertEqual(getattr(user, name), value)

        self.assertEqual(user.gravatar_hash, '5658ffccee7f0ebfda2b226238b1eb6e')
        self.assertEqual(user.about_html, '<p>about_text</p>\n')
