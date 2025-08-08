import os
import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from .models import Exercise
from .forms import ExerciseRequestForm  # Optional, depending on usage

# Load .env and configure OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Utility function to limit exercises for free users
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

@login_required
def generate_exercise(request):
    user = request.user

    if request.method == 'POST':
        topic = request.POST.get('topic', 'chemistry')
        difficulty = request.POST.get('difficulty', user.profile.difficulty or 'intermediate')

        # Check free usage limit
        if not user.profile.has_paid and not can_generate_exercise(user.profile, topic):
            return render(request, 'exercises/result.html', {
                'exercise': '',
                'answer': '',
                'error': f"Free user limit reached for {topic} today. Try again on Monday or Wednesday."
            })

        # Save difficulty
        user.profile.difficulty = difficulty
        user.profile.save()

        # Build and send prompt
        prompt = f"Generate a {difficulty} level high school {topic} exercise with solution. Format clearly with 'Exercise:' and 'Answer:'."
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful teacher."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            parts = content.split("Answer:")
            exercise_part = parts[0].replace("Exercise:", "").strip() if len(parts) > 1 else content
            answer_part = parts[1].strip() if len(parts) > 1 else "Answer not found."

            # Log attempt if free user
            if not user.profile.has_paid:
                topic_data = user.profile.exercise_count.get(topic, {})
                today_str = datetime.date.today().isoformat()
                topic_data[today_str] = topic_data.get(today_str, 0) + 1
                user.profile.exercise_count[topic] = topic_data
                user.profile.save()

            # Save exercise
            Exercise.objects.create(
                user=user,
                topic=topic,
                difficulty=difficulty,
                question=exercise_part,
                answer=answer_part
            )

        except Exception as e:
            exercise_part = "Error:"
            answer_part = str(e)

        return render(request, 'exercises/result.html', {
            'exercise': exercise_part,
            'answer': answer_part
        })

    return render(request, 'exercises/generate.html', {
        'difficulty': user.profile.difficulty
    })

@csrf_exempt
@login_required
def retry_exercise(request):
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
                user=request.user,
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

@login_required
def exercise_history(request):
    exercises = Exercise.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'exercises/history.html', {'exercises': exercises})
