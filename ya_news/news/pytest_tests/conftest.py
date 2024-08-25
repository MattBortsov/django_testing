import datetime
from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.test.client import Client
from django.utils import timezone
from django.urls import reverse

from news.models import Comment, News


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def not_author(django_user_model):
    return django_user_model.objects.create(username='Не автор')


@pytest.fixture
def not_author_client(not_author):
    client = Client()
    client.force_login(not_author)
    return client


@pytest.fixture
def news():
    news = News.objects.create(
        title='Заголовок',
        text='Текст новости',
    )
    return news


@pytest.fixture(scope='function')
@pytest.mark.django_db
def all_news():
    today = datetime.today()
    all_news = [
        News(
            title=f'Тест {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    News.objects.bulk_create(all_news)


@pytest.fixture
def id_for_args(news):
    return (news.id,)


@pytest.fixture
def comment(author, news):
    return Comment.objects.create(
        news=news,
        author=author,
        text='Some comment',
    )


@pytest.fixture
def comments(author, news):
    now = timezone.now()
    for index in range(10):
        comment = Comment.objects.create(
            news=news, author=author, text=f'Tекст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()


@pytest.fixture
def form_data():
    return {'text': 'Beautiful text'}


@pytest.fixture
def url_home():
    return reverse('news:home')


@pytest.fixture
def url_news_detail(id_for_args):
    return reverse('news:detail', args=(id_for_args))


@pytest.fixture
def url_comment_delete(comment):
    return reverse('news:delete', args=(comment.id,))


@pytest.fixture
def url_comment_edit(comment):
    return reverse('news:edit', args=(comment.id,))
