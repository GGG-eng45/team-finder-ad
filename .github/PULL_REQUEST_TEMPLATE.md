## Pull Request: feature/variant2-backend

### Summary
This PR implements Variant 2 (user skills) backend changes for the Team Finder project.

Main features included:
- Custom User model adjustments (name/surname length, phone field normalization, avatar field usage).
- Skill model and UserSkill intermediate model (user.skills accessible via M2M through UserSkill).
- Projects model aligned to spec: status limited to `open`/`closed`, description blankable, participants related_name=`participated_projects`.
- Users endpoints for skill management and filtering:
  - GET `/users/skills/?q=` — autocomplete (up to 10 results, alphabetical)
  - POST `/users/<id>/skills/add` — add skill by id or name
  - POST `/users/<id>/skills/<skill_id>/remove/` — remove skill
  - GET `/users/list/?skill=` — filter users by skill
- Forms validation and normalization:
  - Phone: supports `8XXXXXXXXXX` and `+7XXXXXXXXXX`, normalized to `+7...`, uniqueness enforced
  - GitHub URL validated to point to github.com
  - Registration form saves `username = email` and auto-logs-in user on success
- Automatic avatar generation on user creation (256x256 PNG with initial, deterministic background color)
- Migrations added for changed fields
- README updated with run/test instructions and examples

### Files changed / added (high level)
- users/models.py
- projects/models.py
- users/urls.py
- users/views.py
- users/forms.py
- users/signals.py
- users/apps.py
- users/migrations/0003_alter_fields.py
- projects/migrations/0003_alter_project_fields.py
- readme.md

(See full diff in this branch)

### How to test locally (recommended steps)
1. Copy `.env_example` to `.env` and set required vars.
2. Start services:
   ```bash
   docker-compose up -d
   ```
3. Apply migrations (migrations are committed in this branch):
   ```bash
   docker-compose exec web python manage.py migrate
   ```
4. Create a superuser (optional):
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```
5. Test scenarios:
   - Register a new user via UI → should be auto-logged in and avatar generated in `media/users/avatars/`.
   - Create project via UI or shell and add participants.
   - Autocomplete skills:
     ```bash
     curl "http://localhost:8000/users/skills/?q=Py"
     ```
   - Add skill (authenticated):
     ```bash
     curl -X POST -H "Content-Type: application/json" -d '{"name":"Python"}' http://localhost:8000/users/1/skills/add -b cookiejar -c cookiejar
     ```
   - Remove skill:
     ```bash
     curl -X POST http://localhost:8000/users/1/skills/2/remove/ -b cookiejar -c cookiejar
     ```
   - Filter users:
     ```bash
     curl "http://localhost:8000/users/list/?skill=Python"
     ```

### Checklist for reviewer
- [ ] Code compiles and migrations apply cleanly
- [ ] Registration creates user, auto-login works
- [ ] Avatar file is generated and accessible for new users
- [ ] Skills autocomplete returns correct JSON
- [ ] Add/remove skill endpoints behave as specified (permissions enforced)
- [ ] User list filtering by skill works as intended
- [ ] Phone normalization and GitHub URL validation work and have tests/manual checks

### Notes
- I did not change frontend templates; backend endpoints and JSON responses were aligned to the templates used by the task.
- If you want demo fixtures, I can add a small JSON fixture with a couple of users/skills/projects.

---

If you want me to open the PR on GitHub, I can prepare the PR description here; I do not have a direct tool to create the PR automatically from this environment, so you will need to open it from the branch `feature/variant2-backend` or I can provide the exact API call / UI steps to create it.