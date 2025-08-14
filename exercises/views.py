from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from .models import Exercise, ExerciseRating, SubTopicPerformance
from datetime import date, datetime
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from .forms import ExerciseRequestForm
from accounts.models import Profile  # Adjust if Profile is in another app

# Utility functions
def is_teacher_or_superuser(user):
    return user.is_superuser or user.groups.filter(name='Teachers').exists()

def is_teacher(user):
    return user.is_authenticated and user.groups.filter(name='Teacher').exists()

def is_student(user):
    return not is_teacher_or_superuser(user)

@login_required
def dashboard_router(request):
    user = request.user
    if user.is_superuser:
        return redirect('/admin/')
    if is_teacher(user):
        return redirect('teacher_dashboard')
    return redirect('student_dashboard')

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_superuser:
                return redirect('/admin/')
            elif user.groups.filter(name='Teacher').exists():
                return redirect('teacher_dashboard')
            else:
                return redirect('generate_exercise')
    else:
        form = AuthenticationForm()
    
    return render(request, 'exercises/login.html', {'form': form})

def home_view(request):
    user = request.user
    return render(request, 'exercises/home.html', {
        'is_superuser': user.is_superuser if user.is_authenticated else False,
        'is_teacher': user.groups.filter(name='Teacher').exists() if user.is_authenticated else False,
    })

@login_required
def redirect_after_login(request):
    if request.user.is_superuser:
        return redirect('/admin/')
    elif request.user.groups.filter(name='Teacher').exists():
        return redirect('teacher_dashboard')
    else:
        return redirect('generate_exercise')

@login_required
def admin_dashboard(request):
    return render(request, 'exercises/admin_dashboard.html')

@login_required
def teacher_dashboard(request):
    return render(request, 'exercises/teacher_dashboard.html')

@login_required
def student_dashboard(request):
    return render(request, 'exercises/student_dashboard.html')

@login_required
@user_passes_test(is_teacher_or_superuser)
def update_student_level(request, profile_id):
    profile = Profile.objects.get(id=profile_id)
    if request.method == 'POST':
        new_level = int(request.POST.get('level'))
        profile.chemistry_level = new_level
        profile.save()
        return redirect('teacher_dashboard')
    return render(request, 'exercises/update_level.html', {
        'profile': profile,
        'levels': [(1, 'Beginner'), (2, 'Intermediate'), (3, 'Advanced')]
    })

def can_generate_exercise(profile, topic):
    if profile.has_paid:
        return True
    today = datetime.date.today()
    weekday = today.weekday()  # Monday = 0, Wednesday = 2

    allowed = (weekday == 0 and 2) or (weekday == 2 and 1)
    topic_data = profile.exercise_count.get(topic, {})
    today_count = topic_data.get(today.isoformat(), 0)

    if (weekday == 0 and today_count < 2) or (weekday == 2 and today_count < 1):
        return True
    return False

@login_required(login_url='/exercises/login/')
def generate_exercise(request):
    user = request.user

    if request.method == 'POST':
        student_answer = request.POST.get('student_answer')
        exercise_id = request.POST.get('exercise_id')
        hint_count = int(request.POST.get('hint_count', 0))

        if student_answer and exercise_id:
            try:
                exercise = Exercise.objects.get(id=exercise_id, user=user)
                correct_answer = exercise.answer.strip().lower()
                submitted = student_answer.strip().lower()
                correct = correct_answer == submitted
                rating = 5 - hint_count if correct else 1
                ExerciseRating.objects.update_or_create(
                    user=user,
                    exercise=exercise,
                    defaults={'rating': rating}
                )
                return render(request, 'exercises/result.html', {
                    'exercise': exercise.question,
                    'answer': exercise.answer,
                    'exercise_id': exercise.id,
                    'message': 'Answer submitted successfully!',
                    'rating': rating,
                    'correct': correct,
                    'sub_topic': exercise.sub_topic
                })
            except Exercise.DoesNotExist:
                return render(request, 'exercises/result.html', {
                    'exercise': '',
                    'answer': '',
                    'error': 'Exercise not found.'
                })

        topic = request.POST.get('topic', 'chemistry').lower()
        difficulty = {
            1: 'beginner',
            2: 'intermediate',
            3: 'advanced'
        }.get(user.profile.chemistry_level, 'beginner')

        prompt = (
            f"Generate a {difficulty} level high school {topic} exercise with solution and 3 hints.\n"
            f"Format:\nSub-topic: [subtopic]\nExercise: [statement]\nHint1: [...]\nHint2: [...]\nHint3: [...]\nAnswer: [...]"
        )

        try:
            print("Prompt to GPT:", prompt)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful teacher."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            print("GPT Response:", content)
            sub_topic, question, hint1, hint2, hint3, answer = "", "", "", "", "", ""
            for line in content.splitlines():
                if line.lower().startswith("sub-topic:"):
                    sub_topic = line.split(":", 1)[1].strip()
                elif line.lower().startswith("exercise:"):
                    question = line.split(":", 1)[1].strip()
                elif line.lower().startswith("hint1:"):
                    hint1 = line.split(":", 1)[1].strip()
                elif line.lower().startswith("hint2:"):
                    hint2 = line.split(":", 1)[1].strip()
                elif line.lower().startswith("hint3:"):
                    hint3 = line.split(":", 1)[1].strip()
                elif line.lower().startswith("answer:"):
                    answer = line.split(":", 1)[1].strip()

            exercise_obj = Exercise.objects.create(
                user=user,
                topic=topic,
                sub_topic=sub_topic,
                difficulty=difficulty,
                question=question,
                answer=answer
            )

        except Exception as e:
            return render(request, 'exercises/result.html', {
                'exercise': 'Error generating exercise.',
                'answer': str(e),
                'exercise_id': None,
                'sub_topic': 'General'
            })

        return render(request, 'exercises/result.html', {
            'exercise': question,
            'answer': None,
            'hint1': hint1,
            'hint2': hint2,
            'hint3': hint3,
            'exercise_id': exercise_obj.id,
            'sub_topic': sub_topic,
            'show_answer': False,
            'hint_count': 0
        })

    return render(request, 'exercises/generate.html', {
        'difficulty': user.profile.difficulty,
        'chemistry_level': {
            1: 'Beginner',
            2: 'Intermediate',
            3: 'Advanced'
        }.get(user.profile.chemistry_level, 'Unknown')
    })

@csrf_exempt
@login_required(login_url='/exercises/login/')
def retry_exercise(request):
    user = request.user
    Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        topic = request.POST.get('topic', 'chemistry')
        difficulty = request.POST.get('difficulty', 'intermediate')

        prompt = f"Generate a {difficulty} level high school {topic} exercise with solution. Format clearly with 'Exercise:' and 'Answer:'."

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are a helpful {topic} teacher."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            parts = content.split("Answer:")
            question = parts[0].replace("Exercise:", "").strip() if len(parts) > 1 else content
            answer = parts[1].strip() if len(parts) > 1 else "Answer not found."

            Exercise.objects.create(
                user=user,
                topic=topic,
                difficulty=difficulty,
                question=question,
                answer=answer
            )

            return render(request, 'exercises/result.html', {
                'exercise': question,
                'answer': answer,
                'topic': topic,
                'difficulty': difficulty
            })

        except Exception as e:
            return render(request, 'exercises/result.html', {
                'exercise': '',
                'answer': f"Error: {str(e)}"
            })

@login_required(login_url='/exercises/login/')
def exercise_history(request):
    user = request.user
    Profile.objects.get_or_create(user=user)

    exercises = Exercise.objects.filter(user=user).order_by('-created_at')
    return render(request, 'exercises/history.html', {'exercises': exercises})