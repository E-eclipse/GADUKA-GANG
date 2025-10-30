from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .forms import CustomUserCreationForm
from .models import Section, Topic, UserRankProgress, UserProfile, UserCertificate

User = get_user_model()

def index(request):
    """
    View function for the home page of Gaduka Gang forum
    """
    # Получаем статистику для главной страницы
    stats = {
        'total_users': User.objects.count(),
        'total_topics': Topic.objects.count(),
        'total_posts': 0,  # Нужно будет посчитать реальное количество сообщений
        'online_users': 0,  # Нужно будет реализовать отслеживание онлайн-пользователей
    }
    
    # Получаем последние темы
    latest_topics = Topic.objects.order_by('-created_date')[:5]
    
    # Получаем активных пользователей
    active_users = User.objects.order_by('-last_login')[:10]
    
    # Получаем популярные теги
    # (нужно будет реализовать после создания модели Tag)
    
    context = {
        'stats': stats,
        'latest_topics': latest_topics,
        'active_users': active_users,
    }
    
    return render(request, 'index.html', context)

@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    View function for handling user login
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a success page or the page the user was trying to access
                next_page = request.GET.get('next', 'home')
                return redirect(next_page)
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

@require_http_methods(["GET", "POST"])
def logout_view(request):
    """
    View function for handling user logout
    """
    logout(request)
    return redirect('home')

def register_view(request):
    """
    View function for handling user registration
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаем профиль пользователя
            UserProfile.objects.create(user=user)
            # Автоматически логиним пользователя после регистрации
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})

@login_required
def profile_view(request):
    """
    View function for displaying user profile
    """
    # Ensure user profile exists
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user certificates with related certificate information
    user_certificates = UserCertificate.objects.filter(user=request.user).select_related('certificate')
    
    context = {
        'user_certificates': user_certificates,
    }
    
    return render(request, 'profile.html', context)

@login_required
def edit_profile_view(request):
    """
    View function for editing user profile
    """
    if request.method == 'POST':
        # Get the user profile
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Update profile fields
        user_profile.bio = request.POST.get('bio', user_profile.bio)
        user_profile.signature = request.POST.get('signature', user_profile.signature)
        
        # Update user fields
        request.user.email = request.POST.get('email', request.user.email)
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        
        # Save both user and profile
        request.user.save()
        user_profile.save()
        
        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('profile')
    
    # For GET request, show the edit form
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'user_profile': user_profile,
    }
    
    return render(request, 'edit_profile.html', context)