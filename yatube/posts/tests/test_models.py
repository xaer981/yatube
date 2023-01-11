from django.test import TestCase

from ..constants import CHARS_LIMIT
from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост длиннее 15 символов',
        )

    def test_post_have_correct_objects_names(self):
        """
        Проверяет правильность вывода
        текстового представления объекта Post и Group.
        """
        object_and_expected = {
            str(self.post): self.post.text[:CHARS_LIMIT],
            str(self.group): self.group.title,
        }
        for object, expected in object_and_expected.items():
            with self.subTest(object=object):
                self.assertEqual(expected, object)

    def test_verbose_name(self):
        """
        Проверяет правильность вывода verbose_name объекта Post.
        """
        field_verboses = {
            'text': 'текст поста',
            'author': 'автор поста',
            'group': 'группа поста',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value)

    def test_help_text(self):
        """
        Проверяет правильность вывода help_text объекта Post.
        """
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value)
