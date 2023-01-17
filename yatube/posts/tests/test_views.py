import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..constants import POSTS_LIMIT as FIRST_PAGE_LIMIT
from ..forms import CommentForm, PostForm
from ..models import Comment, Follow, Group, Post, User
from .constants import SECOND_PAGE_LIMIT

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='view_test')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы',
        )
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
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост группы',
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            text='Коммент',
            post=cls.post,
            author=cls.user,
        )

    def setUp(self):
        super().setUp()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def check_post_atributes(self, post):
        """Метод для проверки атрибутов переданного поста."""
        context_and_expected = {
            post.id: self.post.id,
            post.author: self.post.author,
            post.text: self.post.text,
            post.group: self.post.group,
            post.image: self.post.image,
        }

        for context_value, expected_value in context_and_expected.items():
            with self.subTest(field=context_value):
                self.assertEqual(context_value, expected_value)

    def test_pages_correct_template(self):
        """
        Проверяет правильность использования шаблонов
        для view приложения posts.
        """
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={
                    'username': self.user.username}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': self.post.id}): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Проверяет context index: посты."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]

        self.check_post_atributes(post)

    def test_group_list_show_correct_context(self):
        """
        Проверяет context group_list: посты и группу.
        """
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        post = response.context['page_obj'][0]
        group = response.context['group']

        self.check_post_atributes(post)
        self.assertEqual(group, self.group)

    def test_profile_show_correct_context(self):
        """Проверяет context profile: посты, профиль и флаг подписки."""
        follower = User.objects.create_user(username='follower')
        self.authorized_client.force_login(follower)
        Follow.objects.create(
            user=follower,
            author=self.user,
        )

        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        post = response.context['page_obj'][0]
        profile = response.context['profile']
        following = response.context['following']

        self.check_post_atributes(post)
        self.assertEqual(profile, self.user)
        self.assertTrue(following)

    def test_post_detail_show_correct_context(self):
        """
        Проверяет context post_detail:
        пост, выбранный по pk, комментарии и форму создания коммента.
        """
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context['post']
        comment = response.context['comments'][0]
        form = response.context.get('form')

        self.check_post_atributes(post)
        self.assertEqual(comment, self.comment)
        self.assertIsInstance(form, CommentForm)

    def test_post_create_show_correct_context(self):
        """Проверяет context post_create: форму создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form = response.context.get('form')

        self.assertIsInstance(form, PostForm)

    def test_post_edit_show_correct_context(self):
        """
        Проверяет context post_edit: форму редактирования поста,
        флаг редактирования поста (is_edit).
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))

        form = response.context.get('form')
        is_edit = response.context.get('is_edit')
        self.assertIsInstance(form, PostForm)
        self.assertTrue(is_edit)

    def test_new_post_pages(self):
        """
        Проверяет, что новый пост попадает
        на первую позицию index, group_list и profile.
        """
        new_post = Post.objects.create(
            author=self.user,
            text='Тест первой позиции',
            group=self.group,
        )
        addresses = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]

        for url in addresses:
            with self.subTest(url=url):
                response = self.client.get(url)
                context_post = response.context.get('page_obj')[0]
                self.assertEqual(context_post, new_post)

    def test_new_post_not_in_wrong_group(self):
        """
        Проверяет, что пост, опубликованный в новой группе,
        не попадает в group_list старой группы.
        """
        new_group = Group.objects.create(
            title='новая группа',
            slug='new-slug',
            description='описание'
        )
        new_post = Post.objects.create(
            text='пост другой группы',
            author=self.user,
            group=new_group,
        )

        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        context_posts = response.context.get('page_obj')

        self.assertNotIn(new_post, context_posts)

    def test_index_cache(self):
        """Проверяет, что главная страница кэшируется."""
        cached_response = (self.client.get(
            reverse('posts:index'))).content
        Post.objects.create(
            author=self.user,
            text='Тест кэша'
        )
        response_before_cleaning = self.client.get(
            reverse('posts:index')).content
        self.assertEqual(cached_response, response_before_cleaning)
        cache.clear()
        response_after_clearing = self.client.get(
            reverse('posts:index')).content
        self.assertNotEqual(cached_response, response_after_clearing)


class PostsFollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.follower = User.objects.create_user(username='follower')
        cls.post = Post.objects.create(
            text='follow test',
            author=cls.author
        )

    def setUp(self):
        super().setUp()
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

    def test_follow_func(self):
        """Проверяет, что после подписки создаётся объект в Follow."""
        follow_count_before = Follow.objects.count()
        self.assertFalse(Follow.objects.filter(
            user=self.follower, author=self.author).exists())

        self.follower_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author.username}))
        self.assertTrue(Follow.objects.filter(
            user=self.follower, author=self.author).exists())
        self.assertEqual(Follow.objects.count(), follow_count_before + 1)

    def test_unfollow_func(self):
        """Проверяет, что после отписки объект удаляется из Follow."""
        self.assertFalse(Follow.objects.filter(
            user=self.follower, author=self.author).exists())
        Follow.objects.create(
            user=self.follower,
            author=self.author,
        )
        follow_count_before = Follow.objects.count()
        self.follower_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username}))
        self.assertFalse(Follow.objects.filter(
            user=self.follower, author=self.author).exists())
        self.assertEqual(Follow.objects.count(), follow_count_before - 1)

    def test_following_post_exists(self):
        """
        Проверяет, что пост автора,
        на которого подписан юзер, появляется
        в context follow_index.
        """
        Follow.objects.create(
            user=self.follower,
            author=self.author,
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        context_post = response.context.get('page_obj')[0]

        self.assertEqual(context_post, self.post)

    def test_unfollowed_post_doesnt_exists(self):
        """
        Проверяет, что пост автора,
        на которого юзер не подписан,
        не появляется в context follow_index.
        """
        response = self.follower_client.get(reverse('posts:follow_index'))
        context_posts = response.context.get('page_obj')

        self.assertNotIn(self.post, context_posts)


class PostsPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы',
        )
        objs = (Post(author=cls.user,
                     group=cls.group,
                     text=f'пост группы № {i}')
                for i in range(FIRST_PAGE_LIMIT + SECOND_PAGE_LIMIT))
        Post.objects.bulk_create(objs)

    def test_index_paginator(self):
        """
        Проверяет количество постов,
        переданных в paginator context'а страниц index, group_list, profile.
        """
        index_addr = reverse('posts:index')
        group_list_addr = reverse('posts:group_list',
                                  kwargs={'slug': self.group.slug})
        profile_addr = reverse('posts:profile',
                               kwargs={'username': self.user.username})
        second_page_addr = '?page=2'
        addrs_and_expected_objs = {
            index_addr: FIRST_PAGE_LIMIT,
            (index_addr + second_page_addr): SECOND_PAGE_LIMIT,
            group_list_addr: FIRST_PAGE_LIMIT,
            (group_list_addr + second_page_addr): SECOND_PAGE_LIMIT,
            profile_addr: FIRST_PAGE_LIMIT,
            (profile_addr + second_page_addr): SECOND_PAGE_LIMIT,
        }

        for addr, expected_obj in addrs_and_expected_objs.items():
            with self.subTest(addr=addr):
                response = self.client.get(addr)
                self.assertEqual(len(response.context['page_obj']),
                                 expected_obj)
