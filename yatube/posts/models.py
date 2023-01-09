from core.models import CreatedModel
from django.contrib.auth import get_user_model
from django.db import models

from .constants import CHARS_LIMIT

User = get_user_model()


class Group(models.Model):
    """Модель для групп. Имеет название, адрес, описание."""
    title = models.CharField(
        'groups title',
        max_length=200
    )
    slug = models.SlugField(
        'groups slug',
        unique=True
    )
    description = models.TextField('groups description')

    def __str__(self) -> str:

        return self.title


class Post(CreatedModel):
    """
    Модель для постов.
    Имеет текст, дату публикации (автоматически ставится текущее время),
    автора поста(связь с моделью User),
    группу, в которой опубликован пост (связь с моделью Group).
    """
    text = models.TextField(
        'текст поста',
        help_text='Введите текст поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='автор поста'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='группа поста',
        help_text='Группа, к которой будет относиться пост',
        blank=True,
        null=True
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self) -> str:

        return self.text[:CHARS_LIMIT]


class Comment(CreatedModel):
    """
    Модель для комментариев. Имеет текст,
    пост, к которому оставляется комментарий (связь с моделью Post),
    дату публикации (автоматически ставится текущее время)
    и пользователя, оставившего комментарий (связь с моделью User).
    """
    text = models.TextField(
        'текст комментария',
        help_text='Введите текст комментария'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='пост, к которому относится комментарий'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='автор комментария'
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self) -> str:

        return self.text[:CHARS_LIMIT]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='на кого подписка'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
