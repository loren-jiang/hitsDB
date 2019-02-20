#log/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, update_session_auth_hash
from .forms import RegistrationForm, EditUserForm, RecoverUserForm
from .tokens import account_activation_token
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.core.mail import EmailMessage


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
    # https://medium.com/@frfahim/django-registration-with-confirmation-email-bb5da011e4ef 
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = '[hitsDB] Activate your hitsDB account.'
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token':account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            messages.success(request, 'Account created. You will receive \
                a confirmation email to activate your account.')
            return redirect('register')
 
    else:
        form = RegistrationForm()
    return render(request, '../templates/register.html', {'form': form})    

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        update_session_auth_hash(request, user)
        login(request, user)
        # return redirect('home')
        messages.success(request, '[hitsDB] Account has been successfully activated.')
        return redirect('user_home')
    else:
        return HttpResponse('Activation link is invalid!')

def reset_password(request, uidb64, token):
    tempPass = 'User.objects.make_random_password()'
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.set_password(tempPass)
        user.save()
        update_session_auth_hash(request, user)
        login(request, user)
        # return redirect('home')
        return redirect('manage_user')
    else:
        return HttpResponse('Activation link is invalid!')


def user_recover(request):
    if request.method == 'POST':
        usernameInput = request.POST['username']
        
        f = RecoverUserForm(request.POST)
        if f.is_valid():
            # f.save()
            
            user = User.objects.get(username=usernameInput)

            current_site = get_current_site(request)
            mail_subject = '[hitsDB] Password reset.'
            message = render_to_string('resetpw_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token':account_activation_token.make_token(user),
            })
            to_email = user.email
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            messages.success(request, 'Activation email sent to ' + to_email)
            email.send()
            return redirect(reverse('user_recover'))
        # else:
        #     messages.info(request, 'No matching username found.')

    else:
        f = RecoverUserForm()
    data  ={'form': f}
    return render(request,"user_recover.html", data)