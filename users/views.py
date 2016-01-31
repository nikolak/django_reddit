from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest, Http404
from django.shortcuts import render, redirect, get_object_or_404

from reddit.forms import UserForm, ProfileForm
from reddit.utils.helpers import post_only
from users.models import RedditUser


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
        raise Http404

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
                redirect_url = request.POST.get('next') or 'frontpage'
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
    return redirect('frontpage')


def register(request):
    """
    Handles user registration using UserForm from forms.py
    Creates new User and new RedditUser models if appropriate data
    has been supplied.

    If account has been created user is redirected to login page.
    """
    user_form = UserForm()
    if request.user.is_authenticated():
        messages.warning(request,
                        'You are already registered and logged in.')
        return render(request, 'public/register.html', {'form': user_form})

    if request.method == "POST":
        user_form = UserForm(request.POST)

        if user_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            reddit_user = RedditUser()
            reddit_user.user = user
            reddit_user.save()
            user = authenticate(username=request.POST['username'],
                                password=request.POST['password'])
            login(request, user)
            return redirect('frontpage')

    return render(request, 'public/register.html', {'form': user_form})
