from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from projects.models import Project
from users.models import Skill


class Command(BaseCommand):
    help = 'Create demo users, skills and projects for manual testing'

    def handle(self, *args, **options):
        User = get_user_model()

        # Create skills
        skills = ['Python', 'Django', 'JavaScript', 'React', 'DevOps', 'Design']
        skill_objs = []
        for s in skills:
            obj, created = Skill.objects.get_or_create(name=s)
            skill_objs.append(obj)

        # Create users
        users_data = [
            {'email': 'alice@example.com', 'password': 'pass1234', 'name': 'Alice', 'surname': 'Smith', 'phone': '+79001112233'},
            {'email': 'bob@example.com', 'password': 'pass1234', 'name': 'Bob', 'surname': 'Johnson', 'phone': '+79002223344'},
            {'email': 'carol@example.com', 'password': 'pass1234', 'name': 'Carol', 'surname': 'Williams', 'phone': '+79003334455'},
        ]

        created_users = []
        for u in users_data:
            user, created = User.objects.get_or_create(
                email=u['email'],
                defaults={'username': u['email'], 'name': u['name'], 'surname': u['surname'], 'phone': u['phone']}
            )
            if created:
                user.set_password(u['password'])
                user.save()
            created_users.append(user)

        # Assign skills
        if created_users and skill_objs:
            created_users[0].skills.add(skill_objs[0], skill_objs[1])  # Alice: Python, Django
            created_users[1].skills.add(skill_objs[2], skill_objs[3])  # Bob: JavaScript, React
            created_users[2].skills.add(skill_objs[0], skill_objs[4])  # Carol: Python, DevOps

        # Create projects
        if created_users:
            p1, _ = Project.objects.get_or_create(owner=created_users[0], name='Demo Alpha', defaults={'description': 'Alpha project', 'status': 'open'})
            p1.participants.add(*created_users)

        self.stdout.write(self.style.SUCCESS('Demo data created/ensured'))
