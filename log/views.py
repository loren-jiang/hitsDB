#log/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, update_session_auth_hash
from .forms import RegistrationForm, EditUserForm, RecoverUserForm
from django.http import HttpResponseRedirect
from django.urls import reverse

# Create your views here.
# this login required decorator is to not allow to any  
# view without authenticating
@login_required(login_url="login/")
def user_home(request):
    return render(request,"user_home.html")

# @login_required(login_url="login/")
# def view_user(request):
#     user = request.user
#     form = EditUserForm(initial={'username':user.username, 'email':user.email})
#     context = {
#         "form": form
#     }
#     return render(request, 'view_user.html', context)

@login_required(login_url="login/")
def del_user(request, username):
    try:
        u = User.objects.get(username = username)
        u.delete()
        messages.success(request, "The user is deleted")            

    except User.DoesNotExist:
        messages.error(request, "User doesnot exist")    
        return render(request, '/')

    except Exception as e: 
        return render(request, '/',{'err':e.message})

    return render(request, '/') 

def isValidEmail( email ):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email( email )
        return True
    except ValidationError:
        return False

@login_required(login_url="login/")
def manage_user(request):

    user = request.user
    form = EditUserForm(request.POST or None, 
        initial={'email':user.email})

    if request.method == 'POST':
        # newUsername = request.POST['username']
        newEmail = request.POST['email']
        newPassword = request.POST['password1']
        if form.is_valid():

            # user.username = newUsername
            user.email = newEmail
            user.set_password(newPassword)
            user.save()
            messages.success(request,'Account successfully updated.')
            update_session_auth_hash(request, user)
            
            return redirect(reverse('user_home')) #change this to view_user.html
        # else: # a bit hacky for changing just a user's email while keeping username...
        #     if (newUsername == user.username and 
        #         isValidEmail(newEmail)):
        #         user.email = newEmail
        #         user.save()
        #         return HttpResponseRedirect('%s'%(reverse('user_home'))) #change this to view_user.html

    context = {
        "form": form,
        "username": user.username,
        "email": user.email,
        "password": user.password,
    }

    return render(request, "manage_user.html", context)

def register(request):
    if request.method == 'POST':
        f = RegistrationForm(request.POST)
        if f.is_valid():
            f.save()
            messages.success(request, 'Account created successfully')
            return redirect('register')
 
    else:
        f = RegistrationForm()
 
    return render(request, '../templates/register.html', {'form': f})    
    
# this is sort of bad since any non authenticated user can change someone else's password
def user_recover(request):

    if request.method == 'POST':
        usernameInput = request.POST['username']
        
        f = RecoverUserForm(request.POST)
        if f.is_valid():
            # f.save()
            password = User.objects.make_random_password()
            user = User.objects.get(username=usernameInput)
            user.set_password(password)
            user.save()
            messages.success(request, 'New password sent to ' + user.email + 
                user.password)
            return redirect('user_recover')
        else:
            messages.info(request, 'No matching username found.')

    else:
        f = RecoverUserForm()
    data  ={'form': f}
    return render(request,"user_recover.html", data)