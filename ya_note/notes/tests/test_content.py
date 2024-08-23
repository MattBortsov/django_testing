"""
Отдельная заметка передаётся на страницу со списком заметок в списке
object_list в словаре context;
В список заметок одного пользователя не попадают заметки другого пользователя;
На страницы создания и редактирования заметки передаются формы.
"""

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

    def test_note_in_object_list_for_author(self):
        self.client.force_login(self.author)
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertIn('object_list', response.context)
        self.assertIn(self.note, response.context['object_list'])

    def test_note_not_in_object_list_for_non_author(self):
        self.client.force_login(self.not_author)
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertNotIn(self.note, response.context['object_list'])

    def test_add_edit_note_page_contains_form(self):
        self.client.force_login(self.author)
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context.get('form'), NoteForm)
