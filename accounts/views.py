from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.urls import reverse, NoReverseMatch
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Profile
from django.contrib.auth.models import Group

#stripe
import stripe
from django.conf import settings

from .forms import CustomUserCreationForm

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        user_type = request.POST.get('user_type')  # "student" or "teacher"
        if form.is_valid() and user_type in ('student', 'teacher'):
            user = form.save()
            group = Group.objects.get(name='Teacher' if user_type == 'teacher' else 'Student')
            user.groups.add(group)
            login(request, user)
            return redirect('dashboard_router')  # or 'home'
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

from exercises.models import Exercise  # import if not yet done

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

from django.views.decorators.http import require_http_methods

@require_http_methods(['GET','POST'])
def logout_view(request):
    logout(request)
    try:
        return redirect(reverse('home'))
    except NoReverseMatch:
        return redirect('/')

#stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def payment_view(request):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'unit_amount': 1000,  # €10.00
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
            return redirect('generate_exercise')  # or another page
    else:
        form = DifficultyForm(instance=profile)
    return render(request, 'accounts/update_difficulty.html', {'form': form})