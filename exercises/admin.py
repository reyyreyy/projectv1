from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import TopicRatingHistory, SubTopicPerformance
from django.db.models import Avg, Count

@staff_member_required
def teacher_dashboard(request):
    # Average rating per topic over time
    topic_ratings = (
        TopicRatingHistory.objects
        .values('topic')
        .annotate(avg_rating=Avg('rating'), count=Count('id'))
        .order_by('topic')
    )

    # Identify weakest sub-topics across all students
    weak_subtopics = (
        SubTopicPerformance.objects
        .values('topic', 'sub_topic')
        .annotate(
            avg_rating=Avg('total_rating') / Avg('attempt_count'),
            attempts=Sum('attempt_count')
        )
        .filter(attempts__gte=3)
        .order_by('avg_rating')[:5]  # 5 weakest
    )

    return render(request, 'exercises/teacher_dashboard.html', {
        'topic_ratings': topic_ratings,
        'weak_subtopics': weak_subtopics
    })






