from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects, assertFormError

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(
    client, news, form_data, url_news_detail
):
    """Анонимный пользователь не может отправить комментарий."""
    client.post(url_news_detail, form_data)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_can_create_comment(
    author, author_client, news, form_data, url_news_detail
):
    """Авторизованный пользователь может отправить комментарий"""
    response = author_client.post(url_news_detail, form_data)
    assertRedirects(response, f'{url_news_detail}#comments')
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.parametrize('bad_word', BAD_WORDS)
@pytest.mark.django_db
def test_user_cant_use_bad_words(
    author_client, bad_word, news, url_news_detail
):
    """
    Если комментарий содержит запрещённые слова, он не будет опубликован,
    а форма вернёт ошибку.
    """
    bad_words_data = {'text': f'Какой-то текст, {bad_word}, еще текст'}
    response = author_client.post(url_news_detail, data=bad_words_data)
    assertFormError(response, form='form', field='text', errors=WARNING)
    assert Comment.objects.count() == 0


def test_author_can_delete_comment(
    author_client, url_news_detail, url_comment_delete
):
    """Авторизованный пользователь может удалять свои комментарии."""
    response = author_client.delete(url_comment_delete)
    assertRedirects(response, url_news_detail + '#comments')
    assert Comment.objects.count() == 0


def test_user_cant_delete_comment_of_another_user(
    not_author_client, url_comment_delete
):
    """Авторизованный пользователь не может удалять чужие комментарии."""
    response = not_author_client.delete(url_comment_delete)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1


def test_author_can_edit_comment(
    author_client, author, comment, news, form_data,
    url_news_detail, url_comment_edit
):
    """Авторизованный пользователь может редактировать свои комментарии."""
    response = author_client.post(url_comment_edit, form_data)
    assertRedirects(response, url_news_detail + '#comments')
    comment.refresh_from_db()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


def test_user_cant_edit_comment_of_another_user(
    not_author_client, comment, form_data, url_comment_edit
):
    """Авторизованный пользователь не может редактировать чужие комментарии"""
    original_text = comment.text
    original_news = comment.news
    original_author = comment.author
    response = not_author_client.post(url_comment_edit, form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == original_text
    assert comment.news == original_news
    assert comment.author == original_author
