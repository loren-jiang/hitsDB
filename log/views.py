#log/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
# from django.contrib.auth.forms import UserCreationForm
from .forms import RegistrationForm


# Create your views here.
# this login required decorator is to not allow to any  
# view without authenticating
@login_required(login_url="login/")
def user_home(request):
    return render(request,"user_home.html")

@login_required(login_url="login/")
def manage_user(request):
    current_user = request.user
    return render(request,"manage_user.html")

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