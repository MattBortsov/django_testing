from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Boss')
        cls.reader = User.objects.create(username='Bot')
        cls.note = Note.objects.create(
            title='Title',
            text='Text',
            slug='title',
            author=cls.author
        )
        cls.author_client = cls.client_class()
        cls.client_class.force_login(cls.author)
        cls.reader_client = cls.client_class()
        cls.client_class.force_login(cls.reader)

    def test_pages_availability(self):
        """Главная страница, логин, логаут, регистрация доступна всем."""
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """
        Анонимный пользователь перенаправляется на страницу логина,
        при попытке перейти на страницу списка заметок,
        успешного добавления заметки, добавления заметки,
        отдельной заметки, редактирования или удаления заметки.
        """
        login_url = reverse('users:login')
        slug = (self.note.slug,)
        urls = (
            ('notes:add', None),
            ('notes:list', None),
            ('notes:success', None),
            ('notes:edit', slug),
            ('notes:detail', slug),
            ('notes:delete', slug),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_availability_for_note_edit_and_delete(self):
        """
        Аутентифицированному пользователю доступна страница со списком заметок,
        успешного добавления заметки, добавления новой заметки.
        Страницы отдельной заметки, удаления и редактирования заметки
        доступны только автору заметки. Если на эти страницы попытается зайти
        другой пользователь — вернётся ошибка 404.
        """
        user_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.reader_client, HTTPStatus.NOT_FOUND),
        )
        urls = (
            'notes:edit',
            'notes:detail',
            'notes:delete',
        )
        for user, status in user_statuses:
            for name in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)
