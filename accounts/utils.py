import datetime

def can_generate_exercise(profile, topic):
    today = datetime.date.today()
    weekday = today.weekday()  # Monday=0, ..., Sunday=6

    # Limits: 2 on Monday, 1 on Wednesday
    limits = {0: 2, 2: 1}  # Monday and Wednesday

    allowed = limits.get(weekday, 0)

    # Get count from profile
    count_by_topic = profile.exercise_count.get(topic, {})
    today_str = today.isoformat()
    today_count = count_by_topic.get(today_str, 0)

    return today_count < allowed
