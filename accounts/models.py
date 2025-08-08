from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
# accounts/models.py

# class Profile(models.Model):
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    # has_paid = models.BooleanField(default=False)
    # premium_level = models.PositiveSmallIntegerField(default=0)  # 0=Free, 1=1-topic, 2=2-topic, 3=all
    # exercise_count = models.JSONField(default=dict)  # To store count per topic per date
	# difficulty = models.CharField(max_length=20, default="intermediate")
    # math_level = models.IntegerField(default=1)
    # physics_level = models.IntegerField(default=1)
    # chemistry_level = models.IntegerField(default=1)


# from datetime import date

# def can_generate_exercise(self, topic):
    # if self.has_paid:
        # return True  # premium users have no limit

    # today = date.today().isoformat()
    # weekday = date.today().weekday()  # Monday=0, Wednesday=2

    # # Get today's usage for this topic
    # usage = self.exercise_count.get(today, {}).get(topic, 0)

    # # Define limits
    # if weekday == 0 and usage < 2:  # Monday
        # return True
    # elif weekday == 2 and usage < 1:  # Wednesday
        # return True
    # return False

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    has_paid = models.BooleanField(default=False)
    premium_level = models.PositiveSmallIntegerField(default=0)
    exercise_count = models.JSONField(default=dict)
    difficulty = models.CharField(max_length=20, default="intermediate")
    math_level = models.IntegerField(default=1)
    physics_level = models.IntegerField(default=1)
    chemistry_level = models.IntegerField(default=1)

    def can_generate_exercise(self, topic):
        from datetime import date
        if self.has_paid:
            return True

        today = date.today().isoformat()
        weekday = date.today().weekday()

        usage = self.exercise_count.get(today, {}).get(topic, 0)

        if weekday == 0 and usage < 2:  # Monday
            return True
        elif weekday == 2 and usage < 1:  # Wednesday
            return True
        return False





# To store count per topic per date

	
	    # Add this block inside the Profile model
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default='beginner'
    )

    def __str__(self):
        return f"{self.user.username}'s profile"

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            Profile.objects.create(user=instance)




# accounts/models.py

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)



