from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from .models import User

# Create your views here.

def register_view(request):
    if request.method == "POST":
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not firstname or not lastname or not email or not password:
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect('register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return redirect('register')
        
        User.objects.create(
            firstname=firstname,
            lastname=lastname,
            email=email,
            password=make_password(password),
            role="user",
        )
        messages.success(request, "Inscription réussie, vous pouvez vous connecter. ")
        return redirect('login')
        
    return render (request, "accounts/register.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = User.objects.filter(email=email).first()
        if user is not None and check_password(password, user.password):
            request.session['user_id'] = user.id
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, "Email ou mot de passe incorrect. ")
            return redirect('login')
        
    return render (request, "accounts/login.html")

def logout_view(request):
    request.session.flush()
    return redirect('login')