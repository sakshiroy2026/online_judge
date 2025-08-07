from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.template import loader
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
import re
# Create your views here.

def register_user(request):
    if request.method == 'POST':
        first_name= request.POST.get('first_name')
        last_name= request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password=request.POST.get('confirm_password')
        email=request.POST.get('email')
        # Step 2: Check if passwords match
        if password != confirm_password:
            messages.info(request, 'Passwords do not match')
            return redirect("/auth/register/")
        
        # Step 3: Validate email format using regex
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            messages.info(request, 'Invalid email format')
            return redirect("/auth/register/")
        
        if User.objects.filter(email=email).exists():
            messages.info(request, 'Email already registered')
            return redirect("/auth/register/")
        
        user = User.objects.filter(username=username)
        if user.exists():
            messages.info(request, 'User with this username already exists')
            return redirect("/auth/register/")

        user = User.objects.create_user(username=username)
        user.set_password(password)
        user.save()

        messages.info(request, 'User created successfully')
        return redirect('/auth/login')

    template = loader.get_template('sign_up.html')
    context = {}
    return HttpResponse(template.render(context, request))

def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not User.objects.filter(username=username).exists():
            messages.info(request, 'User with this username does not exist')
            return redirect('/auth/login/')

        user = authenticate(username=username, password=password)

        if user is None:
            messages.info(request, 'Invalid password')
            return redirect('/auth/login')

        login(request, user)
        messages.info(request, 'Login successful')

        return redirect('dashboard/')

    template = loader.get_template('login.html')
    context = {}
    return HttpResponse(template.render(context, request))

def logout_user(request):
    logout(request)
    messages.info(request, 'Logout successful')
    return redirect('/auth/login/')

def home(request):
    return render(request, 'home.html')
