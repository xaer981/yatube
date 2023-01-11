import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group_1 = Group.objects.create(
            title='Тестовая группа форм 1',
            slug='test-form-slug-1',
            description='Тестовое описание 1',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа форм 2',
            slug='test-form-slug-2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            text='Ещё тестовый пост',
            group=cls.group_1,
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create_form(self):
        """
        Валидная форма в post_create создаёт запись в Post.
        """
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост формы',
            'group': self.group_1.id,
            'image': uploaded,
        }

        posts_ids_before = list(Post.objects.values_list('id', flat=True))

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), len(posts_ids_before) + 1)
        self.assertTrue(Post.objects.filter(text=form_data['text'],
                                            group_id=form_data['group'],
                                            author=self.user,
                                            image=f'posts/{uploaded.name}')
                        .exclude(id__in=posts_ids_before))

    def test_post_edit_form(self):
        """
        Валидная форма в post_edit редактирует существующую запись в Post.
        """
        editted_data = {
            'text': 'Изменённый пост формы',
            'group': self.group_2.id,
        }

        posts_count = Post.objects.count()

        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}),
            data=editted_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(id=self.post.id,
                                            text=editted_data['text'],
                                            group_id=editted_data['group'],
                                            author=self.user))

    def test_comment_form(self):
        """Варидная форма написания комментария создаёт запись в Comment."""
        form_data = {
            'text': 'Текст коммента',
        }

        comments_ids_before = list(
            Comment.objects.values_list('id', flat=True))

        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(),
                         len(comments_ids_before) + 1)
        self.assertTrue(Comment.objects.filter(text=form_data['text'],
                                               author=self.user,
                                               post=self.post))
