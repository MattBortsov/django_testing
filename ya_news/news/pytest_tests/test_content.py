import pytest
from django.conf import settings
from django.urls import reverse

from news.forms import CommentForm


@pytest.mark.django_db
def test_news_count(all_news, client, url_home):
    """Количество новостей на главной странице — не более 10."""
    response = client.get(url_home)
    assert 'object_list' in response.context, (
        "Ключ 'object_list' отсутствует в контексте ответа"
    )
    object_list = response.context['object_list']
    news_count = object_list.len()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(all_news, client, url_home):
    """Новости отсортированы от самой свежей к самой старой."""
    response = client.get(url_home)
    assert 'object_list' in response.context, (
        "Ключ 'object_list' отсутствует в контексте ответа"
    )
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


def test_comments_order(comments, news, client, url_news_detail):
    """
    Комментарии на странице отдельной новости отсортированы
    в хронологическом порядке: старые в начале списка, новые — в конце.
    """
    response = client.get(url_news_detail)
    assert 'news' in response.context
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, news, url_news_detail):
    """
    Анонимному пользователю недоступна форма для отправки комментария
    на странице отдельной новости.
    """
    response = client.get(url_news_detail)
    assert 'form' not in response.context


def test_authorized_client_has_form(author_client, news, url_news_detail):
    """
    Авторизованному пользователю доступна форма для отправки комментария
    на странице отдельной новости
    """
    response = author_client.get(url_news_detail)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
