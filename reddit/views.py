from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.template.defaulttags import register
from django.http import JsonResponse, HttpResponseBadRequest, Http404, HttpResponseForbidden, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt

from reddit.forms import UserForm, SubmissionForm, ProfileForm
from reddit.models import RedditUser, Submission, Comment, Vote
from reddit.utils.helpers import post_only, get_only


@register.filter
def get_item(dictionary, key):
    """
    Needed because there's no built in .get in django templates
    when working with dictionaries.

    :param dictionary: python dictionary
    :param key: valid dictionary key type
    :return: value of that key or None
    """
    return dictionary.get(key)


def frontpage(request):
    """
    Serves frontpage and all additional submission listings
    with maximum of 25 submissions per page.
    """
    # TODO: Serve user votes on submissions too.

    all_submissions = Submission.objects.order_by('-score').all()
    paginator = Paginator(all_submissions, 25)

    page = request.GET.get('page')
    try:
        submissions = paginator.page(page)
    except PageNotAnInteger:
        submissions = paginator.page(1)
    except EmptyPage:
        submissions = paginator.page(paginator.num_pages)

    submission_votes = {}

    if request.user.is_authenticated():
        for submission in submissions:
            try:
                vote = Vote.objects.get(vote_object_type=submission.get_content_type(),
                                        vote_object_id=submission.id,
                                        user=RedditUser.objects.get(user=request.user))
                submission_votes[submission.id] = vote.value
            except Vote.DoesNotExist:
                pass

    return render(request, 'public/frontpage.html', {'submissions': submissions,
                                                     'submission_votes': submission_votes})


def comments(request, thread_id=None):
    """
    Handles comment view when user opens the thread.
    On top of serving all comments in the thread it will
    also return all votes user made in that thread
    so that we can easily update comments in template
    and display via css whether user voted or not.

    :param thread_id: Thread ID as it's stored in database
    :type thread_id: int
    """

    this_submission = get_object_or_404(Submission, id=thread_id)

    thread_comments = Comment.objects.filter(submission=this_submission)

    if request.user.is_authenticated():
        try:
            reddit_user = RedditUser.objects.get(user=request.user)
        except RedditUser.DoesNotExist:
            reddit_user = None
    else:
        reddit_user = None

    sub_vote_value = None
    try:
        vote = Vote.objects.get(vote_object_type=this_submission.get_content_type(),
                                vote_object_id=this_submission.id)
        sub_vote_value = vote.value
    except Vote.DoesNotExist:
        pass

    comment_votes = {}

    if reddit_user:
        try:
            user_thread_votes = Vote.objects.filter(user=reddit_user,
                                                    submission=this_submission)

            for vote in user_thread_votes:
                comment_votes[vote.vote_object.id] = vote.value
        except:
            pass

    return render(request, 'public/comments.html', {'submission': this_submission,
                                                    'comments': thread_comments,
                                                    'comment_votes': comment_votes,
                                                    'sub_vote': sub_vote_value})


def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = RedditUser.objects.get(user=user)

    return render(request, 'public/profile.html', {'profile': profile})


@login_required
def edit_profile(request):
    user = RedditUser.objects.get(user=request.user)

    if request.method == 'GET':
        profile_form = ProfileForm(instance=user)

    elif request.method == 'POST':
        profile_form = ProfileForm(request.POST, instance=user)
        if profile_form.is_valid():
            profile = profile_form.save(commit=False)
            profile.update_profile_data()
            profile.save()
            messages.success(request, "Profile settings saved")
    else:
        return Http404()

    return render(request, 'private/edit_profile.html', {'form': profile_form})


def user_login(request):
    """
    Pretty straighforward user authentication using password and username
    supplied in the POST request.
    """

    if request.user.is_authenticated():
        messages.warning(request, "You are already logged in.")
        return render(request, 'public/login.html')

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not username or not password:
            return HttpResponseBadRequest()

        user = authenticate(username=username,
                            password=password)

        if user:
            if user.is_active:
                login(request, user)
                redirect_url = request.POST.get('next', 'Frontpage')
                return redirect(redirect_url)
            else:
                return render(request, 'public/login.html',
                              {'login_error': "Account disabled"})
        else:
            return render(request, 'public/login.html',
                          {'login_error': "Wrong username or password."})

    return render(request, 'public/login.html')


@post_only
def user_logout(request):
    """
    Log out user if one is logged in and redirect them to frontpage.
    """

    if request.user.is_authenticated():
        redirect_page = request.POST.get('current_page', '/')
        logout(request)
        messages.success(request, 'Logged out!')
        return redirect(redirect_page)
    return redirect('Frontpage')


def register(request):
    """
    Handles user registration using UserForm from forms.py
    Creates new User and new RedditUser models if appropriate data
    has been supplied.

    If account has been created user is redirected to login page.
    """
    user_form = UserForm()

    if request.method == "POST":
        user_form = UserForm(request.POST)

        if user_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            reddit_user = RedditUser()
            reddit_user.user = user
            reddit_user.save()
            messages.success(request, 'You have successfully registered! You can log in now')
            return redirect('Login')

    return render(request, 'public/register.html', {'form': user_form})


@post_only
def post_comment(request):
    if not request.user.is_authenticated():
        return JsonResponse({'msg': "You need to log in to post new comments."})

    parent_type = request.POST.get('parentType', None)
    parent_id = request.POST.get('parentId', None)
    raw_comment = request.POST.get('commentContent', None)

    if not all([parent_id, parent_type]) or \
                    parent_type not in ['comment', 'submission']:
        return HttpResponseBadRequest()

    if not raw_comment:
        return JsonResponse({'msg': "You have to write something."})
    author = RedditUser.objects.get(user=request.user)
    try:  # try and get comment or submission we're voting on
        if parent_type == 'comment':
            parent_object = Comment.objects.get(id=parent_id)
        elif parent_type == 'submission':
            parent_object = Submission.objects.get(id=parent_id)
        else:
            return HttpResponseBadRequest()

    except (Comment.DoesNotExist, Submission.DoesNotExist):
        return HttpResponseBadRequest()

    comment = Comment.create(author=author,
                             raw_comment=raw_comment,
                             parent=parent_object)

    comment.save()
    return JsonResponse({'msg': "Your comment has been posted."})


@post_only
def vote(request):
    # The type of object we're voting on, can be 'submission' or 'comment'
    vote_object_type = request.POST.get('what', None)

    # The ID of that object as it's stored in the database, positive int
    vote_object_id = request.POST.get('what_id', None)

    # The value of the vote we're writing to that object, -1 or 1
    # Passing the same value twice will cancel the vote i.e. set it to 0
    new_vote_value = request.POST.get('vote_value', None)

    # By how much we'll change the score, used to modify score on the fly
    # client side by the javascript instead of waiting for a refresh.
    vote_diff = 0

    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    else:
        user = RedditUser.objects.get(user=request.user)

    try:  # If the vote value isn't an integer that's equal to -1 or 1
        # the request is bad and we can not continue.
        new_vote_value = int(new_vote_value)

        if new_vote_value not in [-1, 1]:
            raise ValueError("Wrong value for the vote!")

    except ValueError:
        return HttpResponseBadRequest()

    # if one of the objects is None, 0 or some other bool(value) == False value
    # or if the object type isn't 'comment' or 'submission' it's a bad request
    if not all([vote_object_type, vote_object_id, new_vote_value]) or \
                    vote_object_type not in ['comment', 'submission']:
        return HttpResponseBadRequest()

    # Try and get the actual object we're voting on.
    try:
        if vote_object_type == "comment":
            vote_object = Comment.objects.get(id=vote_object_id)

        elif vote_object_type == "submission":
            vote_object = Submission.objects.get(id=vote_object_id)
        else:
            return HttpResponseBadRequest()  # should never happen

    except (Comment.DoesNotExist, Submission.DoesNotExist):
        return HttpResponseBadRequest

    # Try and get the existing vote for this object, if it exists.
    try:
        vote = Vote.objects.get(vote_object_type=vote_object.get_content_type(),
                                vote_object_id=vote_object.id,
                                user=user)

    except Vote.DoesNotExist:
        # Create a new vote and that's it.
        vote = Vote.create(user=user,
                           vote_object=vote_object,
                           vote_value=new_vote_value)
        vote.save()
        vote_diff = new_vote_value
        return JsonResponse({'error': None,
                             'voteDiff': vote_diff})

    # User already voted on this item, this means the vote is either
    # being canceled (same value) or changed (different new_vote_value)
    if vote.value == new_vote_value:
        # canceling vote
        vote_diff = vote.cancel_vote()
        if not vote_diff:
            return HttpResponseBadRequest('Something went wrong while canceling the vote')
    else:
        # changing vote
        vote_diff = vote.change_vote(new_vote_value)
        if not vote_diff:
            return HttpResponseBadRequest('Wrong values for old/new vote combination')

    return JsonResponse({'error': None,
                         'voteDiff': vote_diff})


@login_required
def submit(request):
    """
    Handles new submission.. submission.
    """
    submission_form = SubmissionForm()

    if request.method == 'POST':
        submission_form = SubmissionForm(request.POST)
        if submission_form.is_valid():
            submission = submission_form.save(commit=False)
            submission.generate_html()
            user = User.objects.get(username=request.user)
            redditUser = RedditUser.objects.get(user=user)
            submission.author = redditUser
            submission.author_name = user.username
            submission.save()
            messages.success(request, 'Submission created')
            return redirect('/comments/{}'.format(submission.id))

    return render(request, 'public/submit.html', {'form': submission_form})


@csrf_exempt
def test_data(request):
    """
    Quick and dirty way to create 10 random submissions random comments each
    and up to 100 users with usernames (their passwords are same as usernames)

    Should be removed in production.

    """
    get_page = """
    <form action="/populate/" method="POST">
    Threads: <input type="number" name="threads" value=10></input>
    Root comments: <input type="number" name="comments" value=10></input>
    <button type="submit">Create</button>
    </form>
    """
    if not request.user.is_authenticated() or not request.user.is_staff:
        return Http404()

    if request.method == "GET":
        return HttpResponse(get_page)

    thread_count = int(request.POST.get('threads', 10))
    root_comments = int(request.POST.get('comments', 10))

    from random import choice, randint
    from string import letters

    def get_random_username(length=6):
        return ''.join(choice(letters) for _ in range(length))

    random_usernames = [get_random_username() for _ in range(100)]

    def get_random_sentence(min_words=3, max_words=50,
                            min_word_len=3,
                            max_word_len=15):
        sentence = ''

        for _ in range(0, randint(min_words, max_words)):
            sentence += ''.join(choice(letters)
                                for i in range(randint(min_word_len, max_word_len)))
            sentence += ' '

        return sentence

    def get_or_create_author(username):
        try:
            user = User.objects.get(username=username)
            author = RedditUser.objects.get(user=user)
        except (User.DoesNotExist, RedditUser.DoesNotExist):
            print "Creating user {}".format(username)
            new_author = User(username=username)
            new_author.set_password(username)
            new_author.save()
            author = RedditUser(user=new_author)
            author.save()
        return author

    def add_replies(root_comment, depth=1):
        print "Adding comment replies..."
        if depth > 5:
            return

        comment_author = get_or_create_author(choice(random_usernames))

        raw_text = get_random_sentence()
        new_comment = Comment.create(comment_author, raw_text, root_comment)
        new_comment.save()
        if choice([True, False]):
            add_replies(new_comment, depth + 1)

    for _ in range(thread_count):
        print "Creating new submission."
        selftext = get_random_sentence()
        title = get_random_sentence(max_words=100, max_word_len=10)
        author = get_or_create_author(choice(random_usernames))
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

        for _ in range(root_comments):
            comment_author = get_or_create_author(choice(random_usernames))
            raw_text = get_random_sentence(max_words=100)
            new_comment = Comment.create(comment_author, raw_text, submission)
            new_comment.save()
            another_child = choice([True, False])
            while another_child:
                add_replies(new_comment)
                another_child = choice([True, False])

    return redirect('/')
