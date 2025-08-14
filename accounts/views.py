from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from .models import Profile
from .forms import CustomUserCreationForm
import stripe
from django.conf import settings
from exercises.models import Exercise

@csrf_protect
@require_http_methods(['GET', 'POST'])
def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.get_user())
        return redirect('student_dashboard')
    return render(request, 'accounts/login.html', {'form': form})

@csrf_protect
@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        user_type = request.POST.get('user_type')
        if form.is_valid() and user_type in ['student', 'teacher']:
            user = form.save()
            group = Group.objects.get(name='Teacher' if user_type == 'teacher' else 'Student')
            user.groups.add(group)
            auth_login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def home(request):
    return render(request, 'accounts/home.html')

@login_required
def dashboard(request):
    user = request.user
    difficulty = getattr(user.profile, 'difficulty', 'not set')
    return render(request, 'accounts/dashboard.html', {
        'user': user,
        'difficulty': difficulty
    })

@login_required
def premium_dashboard(request):
    profile = request.user.profile
    selected_difficulty = request.GET.get('difficulty')
    if selected_difficulty:
        exercises = Exercise.objects.filter(user=request.user, difficulty=selected_difficulty)
    else:
        exercises = Exercise.objects.filter(user=request.user)
    return render(request, 'accounts/premium_dashboard.html', {
        'user': request.user,
        'difficulty': profile.difficulty,
        'exercises': exercises,
        'selected_difficulty': selected_difficulty,
    })

def logout_view(request):
    logout(request)
    return redirect('login')

stripe.api_key = settings.STRIPE_SECRET_KEY

def payment_view(request):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'unit_amount': 1000,
                'product_data': {
                    'name': 'Access to Course',
                },
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='http://127.0.0.1:8000/success/',
        cancel_url='http://127.0.0.1:8000/cancel/',
    )
    return render(request, 'payment.html', {
        'session_id': session.id,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    })

from .forms import DifficultyForm

@login_required
def update_difficulty(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = DifficultyForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('generate_exercise')
    else:
        form = DifficultyForm(instance=profile)
    return render(request, 'accounts/update_difficulty.html', {'form': form})