# Team Finder (Variant 2) — Backend

This repository implements the backend for the Team Finder project (variant 2 — user skills).

What is implemented
- Custom User model with fields required by the task (name, surname, avatar, phone, github_url, about).
- Skill model and UserSkill intermediate model (user.skills accessible via M2M through UserSkill).
- Project model with fields: name, description, owner, github_url, status (only `open` or `closed`), participants (related_name `participated_projects`).
- Endpoints for skills autocomplete and management:
  - GET  /users/skills/?q=<query>  — returns up to 10 matching skills (alphabetical). Response format: [{"id":<id>,"name":"<name>"}, ...]
  - POST /users/<user_id>/skills/add  — add skill to the user (accepts JSON or form: {"skill_id":<id>} or {"name":"<name>"}). Response: {"skill_id":<id>,"created":<bool>,"added":<bool>}.
  - POST /users/<user_id>/skills/<skill_id>/remove/ — remove skill from user. Response: {"removed": true}
- User list with optional filter: GET /users/list/?skill=<skill_name> — renders participants template with context {"participants": <page_obj>, "all_skills": <all skills>, "active_skill": <filter>}.
- Forms validation:
  - Phone normalized: accepts 8XXXXXXXXXX or +7XXXXXXXXXX and normalizes to +7XXXXXXXXXX; uniqueness enforced.
  - github_url validated to point to github.com.
- Automatic avatar generation on user creation: 256×256 PNG with first letter on deterministic background color.

Run locally (with Docker Compose)
1. Copy `.env_example` to `.env` and adjust values if needed.
2. Start containers:

   docker-compose up -d

3. Run migrations:

   docker-compose exec web python manage.py migrate

4. Create a superuser (optional):

   docker-compose exec web python manage.py createsuperuser

Manual creation of users and projects (example)
1. Open Django shell:

   docker-compose exec web python manage.py shell

2. Example commands:

   from django.contrib.auth import get_user_model
   from projects.models import Project
   User = get_user_model()

   # create user (username == email)
   u = User.objects.create_user(username='maria@example.com', email='maria@example.com', password='pass1234', name='Maria', surname='Ivanova', phone='+79001234567')

   # create project
   p = Project.objects.create(owner=u, name='Demo Project', description='Описание', github_url='', status='open')
   p.participants.add(u)

   exit()

API examples (curl)
- Autocomplete skills:

  curl "http://localhost:8000/users/skills/?q=Py"

- Add skill by name (JSON):

  curl -X POST -H "Content-Type: application/json" -d '{"name":"Python"}' http://localhost:8000/users/1/skills/add -b cookiejar -c cookiejar

  Note: adding/removing skills requires authentication. Use cookie-based session or include appropriate credentials.

- Remove skill:

  curl -X POST http://localhost:8000/users/1/skills/2/remove/ -b cookiejar -c cookiejar

Notes
- I intentionally did not modify frontend templates (templates_var2). The backend URLs and JSON formats were aligned to match the templates expected by the task.
- Migrations for the changes are added to the repository (see `users/migrations/0003_*` and `projects/migrations/0001_*`).

If you want me to run the app locally and verify interactions or create demo fixtures, tell me and I will proceed (I used docker-compose present in the repository to prepare everything).