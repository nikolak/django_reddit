from random import choice, randint
from string import ascii_letters as letters

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from reddit.models import Comment
from reddit.models import Submission
from users.models import RedditUser


class Command(BaseCommand):
    help = 'Generates tests data'

    def add_arguments(self, parser):
        parser.add_argument('--thread_count', type=int, default=10)
        parser.add_argument('--root_comments', type=int, default=10)

    def handle(self, *args, **options):
        self.thread_count = options['thread_count']
        self.root_comments = options['root_comments']
        self. random_usernames = [self.get_random_username() for _ in range(100)]
        for index, _ in enumerate(range(self.thread_count)):
            print("Thread {} out of {}".format(str(index), self.thread_count))
            selftext = self.get_random_sentence()
            title = self.get_random_sentence(max_words=100, max_word_len=10)
            author = self.get_or_create_author(choice(self.random_usernames))
            ups = randint(0, 1000)
            url = None
            downs = int(ups) / 2
            comments = 0

            submission = Submission(author=author,
                                    title=title,
                                    url=url,
                                    text=selftext,
                                    ups=int(ups),
                                    downs=downs,
                                    score=ups - downs,
                                    comment_count=comments)
            submission.generate_html()
            submission.save()

            for _ in range(self.root_comments):
                print("Adding thread comments...")
                comment_author = self.get_or_create_author(choice(self.random_usernames))
                raw_text = self.get_random_sentence(max_words=100)
                new_comment = Comment.create(comment_author, raw_text, submission)
                new_comment.save()
                another_child = choice([True, False])
                while another_child:
                    self.add_replies(new_comment)
                    another_child = choice([True, False])

    def get_random_username(self, length=6):
        return ''.join(choice(letters) for _ in range(length))

    def get_random_sentence(min_words=3, max_words=50,
                            min_word_len=3,
                            max_word_len=15):
        sentence = ''

        for _ in range(0, randint(min_words, max_words)):
            sentence += ''.join(choice(letters)
                                for i in
                                range(randint(min_word_len, max_word_len)))
            sentence += ' '

        return sentence

    def get_or_create_author(self, username):
        try:
            user = User.objects.get(username=username)
            author = RedditUser.objects.get(user=user)
        except (User.DoesNotExist, RedditUser.DoesNotExist):
            print("Creating user {}".format(username))
            new_author = User(username=username)
            new_author.set_password(username)
            new_author.save()
            author = RedditUser(user=new_author)
            author.save()
        return author

    def add_replies(self, root_comment, depth=1):
        if depth > 5:
            return

        comment_author = self.get_or_create_author(choice(self.random_usernames))

        raw_text = self.get_random_sentence()
        new_comment = Comment.create(comment_author, raw_text, root_comment)
        new_comment.save()
        if choice([True, False]):
            self.add_replies(new_comment, depth + 1)
