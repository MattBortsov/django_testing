"""
Анонимный пользователь не может отправить комментарий,
а авторизованный - может.
Если комментарий содержит запрещённые слова, он не будет опубликован,
а форма вернёт ошибку.
Авторизованный пользователь может редактировать или удалять свои комментарии,
а чужие - нет.
"""

import pytest
from http import HTTPStatus

from django.urls import reverse

from pytest_django.asserts import assertRedirects

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news, form_data):
    url = reverse('news:detail', args=(news.id,))
    client.post(url, form_data)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_can_create_comment(author, author_client, news, form_data):
    url = reverse('news:detail', args=(news.id,))
    response = author_client.post(url, form_data)
    assertRedirects(response, f'{url}#comments')
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_user_cant_use_bad_words(author_client, news):
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    url = reverse('news:detail', args=(news.id,))
    response = author_client.post(url, data=bad_words_data)
    assert 'form' in response.context
    form = response.context['form']
    assert form.errors['text'] == [WARNING]
    assert Comment.objects.count() == 0


def test_author_can_delete_comment(author_client, comment, news):
    url = reverse('news:detail', args=(news.id,))
    delete_url = reverse('news:delete', args=(comment.id,))
    response = author_client.delete(delete_url)
    assertRedirects(response, url + '#comments')
    assert Comment.objects.count() == 0


def test_user_cant_delete_comment_of_another_user(not_author_client, comment):
    delete_url = reverse('news:delete', args=(comment.id,))
    response = not_author_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1


def test_author_can_edit_comment(author_client, comment, news, form_data):
    url = reverse('news:detail', args=(news.id,))
    edit_url = reverse('news:edit', args=(comment.id,))
    response = author_client.post(edit_url, form_data)
    assertRedirects(response, url + '#comments')
    comment.refresh_from_db()
    assert comment.text == form_data['text']


def test_user_cant_edit_comment_of_another_user(
        not_author_client, comment, form_data, comment_text
):
    edit_url = reverse('news:edit', args=(comment.id,))
    response = not_author_client.post(edit_url, form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == comment_text
