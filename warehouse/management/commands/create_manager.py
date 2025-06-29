from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a warehouse manager user with staff privileges'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the manager')
        parser.add_argument('email', type=str, help='Email for the manager')
        parser.add_argument('--password', type=str, help='Password (if not provided, will prompt)')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options.get('password')

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'User "{username}" already exists.')
            )
            return

        if not password:
            password = input('Enter password for the manager: ')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,  # This gives warehouse access
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created warehouse manager "{username}" with staff privileges.\n'
                f'This user can now access the warehouse system at /warehouse/'
            )
        )
