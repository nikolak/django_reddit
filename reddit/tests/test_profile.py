from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.contrib.auth.models import User
from reddit.models import RedditUser
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

class TestProfileEditingForm(TestCase):

    def test_all_valid_data(self):
        test_data = {
            'first_name':'first_name',
            'last_name':'last_name',
            'email':'email@example.com',
            'display_picture':False,
            'about_text':'about_text',
            'homepage':'http://example.com',
            'github':'username',
            'twitter':'username',
        }
        form = ProfileForm(data=test_data)
        self.assertTrue(form.is_valid())

    def test_invalid_data(self):
        test_data = {
            'first_name':'too_long_first_name',
            'last_name':'too_long_last_name',
            'email':'notanemail',
            'display_picture':False,
            'about_text':'toolong'*75,
            'homepage':'notadomain',
            'github':'toolong'*10,
            'twitter':'toolong'*5,
        }
        form = ProfileForm(data=test_data)
        self.assertEqual(form.errors['first_name'], [u"Ensure this value has at most 12 characters (it has 19)."])
        self.assertEqual(form.errors['last_name'], [u"Ensure this value has at most 12 characters (it has 18)."])
        self.assertEqual(form.errors['email'], [u"Enter a valid email address."])
        self.assertEqual(form.errors['about_text'], [u"Ensure this value has at most 500 characters (it has 525)."])
        self.assertEqual(form.errors['homepage'], [u"Enter a valid URL."])
        self.assertEqual(form.errors['github'], [u"Ensure this value has at most 39 characters (it has 70)."])
        self.assertEqual(form.errors['twitter'], [u"Ensure this value has at most 15 characters (it has 35)."])
        self.assertFalse(form.is_valid())

    def test_empty_data(self):
        test_data = {
            'first_name':'',
            'last_name':'',
            'email':'',
            'display_picture':False,
            'about_text':'',
            'homepage':'',
            'github':'',
            'twitter':'',
        }
        form = ProfileForm(data=test_data)
        self.assertTrue(form.is_valid())