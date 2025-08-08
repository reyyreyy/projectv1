from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from datetime import date, datetime
from openai import OpenAI
from accounts.models import Profile
from .models import Exercise, ExerciseRating, SubTopicPerformance, TopicRatingHistory

client = OpenAI()

@login_required(login_url='/exercises/login/')
def generate_exercise(request):
    user = request.user
    # ✅ Ensure profile exists
    Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # 🟡 1. Handle Rating Submission
        if 'rate' in request.POST:
            exercise_id = request.POST.get('exercise_id')
            rating_value = int(request.POST.get('rating', 0))

            try:
                exercise = Exercise.objects.get(id=exercise_id, user=user)
                ExerciseRating.objects.update_or_create(
                    user=user,
                    exercise=exercise,
                    defaults={'rating': rating_value}
                )

                # 📊 Update Sub-topic performance
                sub_topic = exercise.sub_topic or "General"
                perf, _ = SubTopicPerformance.objects.get_or_create(
                    user=user,
                    topic=exercise.topic,
                    sub_topic=sub_topic
                )
                perf.attempt_count += 1
                perf.total_rating += rating_value
                perf.save()

                # 📈 Save topic-wide rating history
                TopicRatingHistory.objects.create(
                    user=user,
                    topic=exercise.topic,
                    rating=rating_value,
                    timestamp=datetime.now()
                )

                # 📉 Suggest weak sub-topic if needed
                suggestion = None
                weak = SubTopicPerformance.objects.filter(
                    user=user,
                    topic=exercise.topic,
                    attempt_count__gte=1
                ).order_by('total_rating')

                for w in weak:
                    avg_rating = w.total_rating / w.attempt_count if w.attempt_count else 0
                    if avg_rating < 3:
                        suggestion = f"We recommend reviewing the sub-topic: {w.sub_topic}"
                        break

                # Adjust level based on rating (Chemistry only)
                if exercise.topic.lower() == 'chemistry':
                    current_level = user.profile.chemistry_level
                    if rating_value >= 4 and current_level < 3:
                        user.profile.chemistry_level += 1
                    elif rating_value <= 2 and current_level > 1:
                        user.profile.chemistry_level -= 1
                    user.profile.save()

                return render(request, 'exercises/result.html', {
                    'exercise': exercise.question,
                    'answer': exercise.answer,
                    'exercise_id': exercise.id,
                    'message': 'Rating submitted successfully!',
                    'sub_topic': exercise.sub_topic,
                    'suggestion': suggestion
                })

            except Exercise.DoesNotExist:
                return render(request, 'exercises/result.html', {
                    'exercise': '',
                    'answer': '',
                    'error': 'Exercise not found for rating.'
                })

        # 🟢 2. Handle Exercise Generation
        topic = request.POST.get('topic', 'chemistry').lower()
        difficulty = request.POST.get('difficulty') or {
            1: 'beginner',
            2: 'intermediate',
            3: 'advanced'
        }.get(user.profile.chemistry_level, 'intermediate')

        if not user.profile.has_paid:
            today = date.today()
            weekday = today.strftime("%A")
            exercise_data = user.profile.exercise_count
            today_str = str(today)

            if today_str not in exercise_data:
                exercise_data[today_str] = {}

            topic_count = exercise_data[today_str].get(topic, 0)
            allowed = (weekday == "Monday" and topic_count < 2) or (weekday == "Wednesday" and topic_count < 1)

            if not allowed:
                return render(request, 'exercises/result.html', {
                    'exercise': None,
                    'answer': None,
                    'error': f"Free users can only generate limited {topic.title()} exercises on {weekday}s."
                })

            exercise_data[today_str][topic] = topic_count + 1
            user.profile.exercise_count = exercise_data
            user.profile.save()

        user.profile.difficulty = difficulty
        user.profile.save()

        # Step 3: Prompt with Sub-topic instruction
        prompt = (
            f"Generate a {difficulty} level high school {topic} exercise with solution. "
            f"Start with a line like 'Sub-topic: [e.g. Thermochemistry]'. "
            f"Then format clearly with 'Exercise:' and 'Answer:'."
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful teacher."},
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.choices[0].message.content

            # 🖚 Extract sub-topic
            sub_topic = "General"
            for line in content.splitlines():
                if line.strip().lower().startswith("sub-topic:"):
                    sub_topic = line.split(":", 1)[1].strip()
                    break

            # Extract exercise and answer
            parts = content.split("Answer:")
            exercise_part = parts[0].split("Exercise:")[-1].strip() if "Exercise:" in parts[0] else parts[0]
            answer_part = parts[1].strip() if len(parts) > 1 else "Answer not found."

            exercise_obj = Exercise.objects.create(
                user=user,
                topic=topic,
                sub_topic=sub_topic,
                difficulty=difficulty,
                question=exercise_part,
                answer=answer_part
            )

        except Exception as e:
            exercise_part = "Error:"
            answer_part = str(e)
            exercise_obj = None
            sub_topic = "General"

        return render(request, 'exercises/result.html', {
            'exercise': exercise_part,
            'answer': answer_part,
            'exercise_id': exercise_obj.id if exercise_obj else None,
            'sub_topic': sub_topic,
            'suggestion': None
        })

    # GET request — show form
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
    # ✅ Ensure profile exists
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
    # ✅ Ensure profile exists
    Profile.objects.get_or_create(user=user)

    exercises = Exercise.objects.filter(user=user).order_by('-created_at')
    return render(request, 'exercises/history.html', {'exercises': exercises})
