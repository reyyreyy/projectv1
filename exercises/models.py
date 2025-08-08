from django.db import models

# Create your models here.
from django.contrib.auth.models import User


class TopicRatingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=100)
    rating = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.topic} - {self.rating}"



# class GeneratedExercise(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    # topic = models.CharField(max_length=100, default="chemistry")
    # difficulty = models.CharField(max_length=20)
    # question = models.TextField()
    # answer = models.TextField()
    # created_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
        # return f"{self.topic} ({self.difficulty}) on {self.created_at.date()}"


class Exercise(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=100)  # e.g. 'chemistry'
    sub_topic = models.CharField(max_length=100, default='General')  # ← NEW FIELD
    difficulty = models.CharField(max_length=20)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.topic} ({self.difficulty})"


class ExerciseRating(models.Model):
    exercise = models.ForeignKey('Exercise', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=0)  # 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('exercise', 'user')  # Prevent double rating

    def __str__(self):
        return f"{self.user.username} rated {self.exercise.id} - {self.rating}"


class SubTopicPerformance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=100)  # e.g. 'chemistry'
    sub_topic = models.CharField(max_length=100)
    attempt_count = models.PositiveIntegerField(default=0)
    total_rating = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'topic', 'sub_topic')

    def average_rating(self):
        return self.total_rating / self.attempt_count if self.attempt_count else 0

    def __str__(self):
        return f"{self.user.username} - {self.topic}/{self.sub_topic} ({self.attempt_count} attempts)"
