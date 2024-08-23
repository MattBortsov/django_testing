"""
Залогиненный пользователь может создать заметку, а анонимный — не может.
Невозможно создать две заметки с одинаковым slug.
Если при создании заметки не заполнен slug, то он формируется автоматически,
с помощью функции pytils.translit.slugify.
Пользователь может редактировать и удалять свои заметки,
но не может редактировать или удалять чужие.
"""

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()


class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author')
        cls.not_author = User.objects.create(username='Not author')
        cls.note = Note.objects.create(
            title='Title',
            text='Text',
            slug='slug',
            author=cls.author
        )

    def test_user_can_create_note(self):
        self.client.force_login(self.author)
        url = reverse('notes:add')
        data = {'title': 'New Note', 'text': 'Some text'}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertTrue(Note.objects.filter(title='New Note').exists())

    def test_anonymous_user_cant_create_note(self):
        url = reverse('notes:add')
        data = {'title': 'New Note', 'text': 'Some text'}
        response = self.client.post(url, data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertFalse(Note.objects.filter(title='New Note').exists())

    def test_not_unique_slug(self):
        self.client.force_login(self.author)
        url = reverse('notes:add')
        data = {
            'title': 'Note with auto slug',
            'text': 'Some text',
            'slug': 'slug'
        }
        response = self.client.post(url, data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        self.client.force_login(self.author)
        url = reverse('notes:add')
        data = {
            'title': 'New Title',
            'text': 'Some text'
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.exclude(id=self.note.id).latest('id')
        expected_slug = slugify(data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_user_can_edit_own_note(self):
        self.client.force_login(self.author)
        url = reverse('notes:edit', args=(self.note.slug,))
        data = {
            'title': 'Updated Note',
            'text': 'Updated text',
            'slug': 'slug'
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, data['title'])
        self.assertEqual(self.note.text, data['text'])
        self.assertEqual(self.note.slug, data['slug'])

    def test_user_cannot_edit_others_note(self):
        self.client.force_login(self.not_author)
        url = reverse('notes:edit', args=(self.note.slug,))
        data = {
            'title': 'Attempted Edit',
            'text': 'Attempted text',
            'slug': 'slug'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(note_from_db.title, self.note.title)
        self.assertEqual(note_from_db.text, self.note.text)
        self.assertEqual(note_from_db.slug, self.note.slug)

    def test_user_can_delete_own_note(self):
        self.client.force_login(self.author)
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertFalse(Note.objects.filter(slug=self.note.slug).exists())

    def test_user_cannot_delete_others_note(self):
        self.client.force_login(self.not_author)
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
