import os
import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from users.models import Skill, UserSkill
from users.forms import ProfileEditForm

User = get_user_model()


class FormsTests(TestCase):
    def test_phone_normalization_and_uniqueness(self):
        u = User.objects.create_user(username='exist@example.com', email='exist@example.com', password='pass', phone='+79001112233')
        # editing another user with same phone should raise
        form = ProfileEditForm(data={'name': 'X', 'surname': 'Y', 'about': '', 'phone': '8' + '9001112233', 'github_url': ''}, instance=User())
        # since instance is not saved, uniqueness check will consider existing user and should raise
        with self.assertRaises(Exception):
            form.is_valid()

    def test_github_url_validation(self):
        form = ProfileEditForm(data={'name': 'A', 'surname': 'B', 'about': '', 'phone': '+79009998877', 'github_url': 'https://gitlab.com/user'})
        self.assertFalse(form.is_valid())
        self.assertIn('github_url', form.errors)


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class SignalsTests(TestCase):
    def tearDown(self):
        # clean up any avatars created in temp dir
        media_tmp = tempfile.gettempdir()
        avatars_dir = os.path.join(media_tmp, 'users', 'avatars')
        if os.path.exists(avatars_dir):
            shutil.rmtree(os.path.join(media_tmp, 'users'))

    def test_avatar_generated_on_user_create(self):
        u = User.objects.create_user(username='new@example.com', email='new@example.com', password='pass', name='New', surname='User')
        # reload from db
        u.refresh_from_db()
        self.assertTrue(bool(u.avatar), 'Avatar field should be set by signal')
        # file should exist on disk
        self.assertTrue(os.path.exists(u.avatar.path))


class ViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice@example.com', email='alice@example.com', password='pass')
        # create some skills
        self.skill_python = Skill.objects.create(name='Python')
        self.skill_django = Skill.objects.create(name='Django')

    def test_search_skills(self):
        url = reverse('users:search_skills')
        response = self.client.get(url, {'q': 'Py'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(isinstance(data, list))
        self.assertGreaterEqual(len(data), 1)
        names = [it['name'] for it in data]
        self.assertIn('Python', names)

    def test_add_skill_requires_login_and_adds(self):
        url = reverse('users:add_skill', kwargs={'user_id': self.user.id})
        # try without login
        response = self.client.post(url, {'name': 'Go'})
        self.assertEqual(response.status_code, 302)  # redirect to login

        # login and add
        self.client.login(username='alice@example.com', password='pass')
        response = self.client.post(url, {'name': 'Go'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('skill_id', data)
        # skill should be linked
        skill_id = data['skill_id']
        self.assertTrue(UserSkill.objects.filter(user=self.user, skill_id=skill_id).exists())

    def test_remove_skill(self):
        # add a skill first
        us = UserSkill.objects.create(user=self.user, skill=self.skill_python)
        url = reverse('users:remove_skill', kwargs={'user_id': self.user.id, 'skill_id': self.skill_python.id})
        # without login
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        # login and remove
        self.client.login(username='alice@example.com', password='pass')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(UserSkill.objects.filter(pk=us.pk).exists())
