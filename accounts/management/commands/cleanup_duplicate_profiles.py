from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile

class Command(BaseCommand):
    help = 'Remove duplicate profiles and ensure each user has only one profile.'

    def handle(self, *args, **kwargs):
        for user in User.objects.all():
            profiles = Profile.objects.filter(user=user)
            if profiles.count() > 1:
                self.stdout.write(f'Cleaning duplicates for user: {user.username}')
                # Keep only the first profile and delete the rest
                first = profiles.first()
                duplicates = profiles.exclude(id=first.id)
                duplicates.delete()
        self.stdout.write('Duplicate profile cleanup complete.')
