from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed admin account for hackathon demo'

    def handle(self, *args, **kwargs):
        email = 'admin@admin.com'
        password = 'admin123'

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'Admin user {email} already exists'))
            return

        admin = User.objects.create_superuser(
            username='admin',
            email=email,
            password=password,
            is_merchant=True,
        )
        self.stdout.write(self.style.SUCCESS(f'Admin created: {email} / {password}'))
