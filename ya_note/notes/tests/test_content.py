from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Autor')
        cls.not_author = User.objects.create(username='Not author')
        cls.note = Note.objects.create(
            title='title',
            text='text',
            slug='title',
            author=cls.author
        )
        cls.author_client = cls.client_class()
        cls.author_client.force_login(cls.author)
        cls.not_author_client = cls.client_class()
        cls.not_author_client.force_login(cls.not_author)

    def test_note_in_object_list_for_users(self):
        """
        В список заметок одного пользователя
        не попадают заметки другого пользователя.
        Отдельная заметка передаётся на страницу со списком заметок.
        """
        clients = (
            (self.author_client, True),
            (self.not_author_client, False)
        )
        url = reverse('notes:list')
        for client, expected_status in clients:
            with self.subTest(client=client):
                response = client.get(url)
                object_list = response.context.get('object_list', [])
                self.assertIs(self.note in object_list, expected_status)

    def test_add_edit_note_page_contains_form(self):
        """На страницы создания и редактирования заметки передаются формы."""
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context.get('form'), NoteForm)
