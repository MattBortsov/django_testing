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
        cls.author_client = cls.client_class()
        cls.author_client.force_login(cls.author)
        cls.not_author_client = cls.client_class()
        cls.not_author_client.force_login(cls.not_author)
        cls.form_data = {
            'title': 'Note with auto slug',
            'text': 'Some text',
            'slug': 'slug'
        }
        cls.empty_slug_data = {
            'title': 'New Title',
            'text': 'Some text'
        }

    def test_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        url = reverse('notes:add')
        Note.objects.all().delete()
        response = self.author_client.post(url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        new_note = Note.objects.get(title=self.form_data['title'])
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        url = reverse('notes:add')
        initial_count = Note.objects.count()
        response = self.client.post(url, self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), initial_count)

    def test_not_unique_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        url = reverse('notes:add')
        initial_count = Note.objects.count()
        response = self.author_client.post(url, self.form_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), initial_count)

    def test_empty_slug(self):
        """
        Если при создании заметки не заполнен slug,
        то он формируется автоматически.
        """
        url = reverse('notes:add')
        response = self.author_client.post(url, self.empty_slug_data)
        self.assertRedirects(response, reverse('notes:success'))
        new_note = Note.objects.get(title=self.empty_slug_data['title'])
        expected_slug = slugify(self.empty_slug_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_user_can_edit_own_note(self):
        """Пользователь может редактировать свои заметки."""
        url = reverse('notes:edit', args=(self.note.slug,))
        data = {
            'title': 'Updated Note',
            'text': 'Updated text',
            'slug': 'slug'
        }
        response = self.author_client.post(url, data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, data['title'])
        self.assertEqual(self.note.text, data['text'])
        self.assertEqual(self.note.slug, data['slug'])

    def test_user_cannot_edit_others_note(self):
        """Пользователь не может редактировать чужие заметки."""
        url = reverse('notes:edit', args=(self.note.slug,))
        data = {
            'title': 'Attempted Edit',
            'text': 'Attempted text',
            'slug': 'slug'
        }
        response = self.not_author_client.post(url, data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(note_from_db.title, self.note.title)
        self.assertEqual(note_from_db.text, self.note.text)
        self.assertEqual(note_from_db.slug, self.note.slug)

    def test_user_can_delete_own_note(self):
        """Пользователь может удалять свои заметки."""
        url = reverse('notes:delete', args=(self.note.slug,))
        initial_count = Note.objects.count()
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), initial_count - 1)

    def test_user_cannot_delete_others_note(self):
        """Пользователь не может удалять чужие заметки."""
        url = reverse('notes:delete', args=(self.note.slug,))
        initial_count = Note.objects.count()
        response = self.not_author_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), initial_count)
