import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..constants import POSTS_LIMIT as FIRST_PAGE_LIMIT
from ..forms import PostForm
from ..models import Comment, Group, Post, User
from .constants import SECOND_PAGE_LIMIT

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostsPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='view_test')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост группы',
        )

    def check_post_atributes(self, post):
        """Метод для проверки атрибутов переданного поста."""
        context_and_expected = {
            post.id: self.post.id,
            post.author: self.post.author,
            post.text: self.post.text,
            post.group: self.post.group,
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
        """Проверяет context profile: посты и профиль."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        post = response.context['page_obj'][0]
        profile = response.context['profile']

        self.check_post_atributes(post)
        self.assertEqual(profile, self.user)

    def test_post_detail_show_correct_context(self):
        """Проверяет context post_detail: пост, выбранный по pk."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context['post']

        self.check_post_atributes(post)

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

    def test_new_post_index(self):
        """
        Проверяет, что новый пост попадает на первую позицию index.
        """
        new_post = Post.objects.create(
            author=self.user,
            text='Тест индекс',
            group=self.group,
        )
        response = self.client.get(reverse('posts:index'))
        context_post = response.context.get('page_obj')[0]

        self.assertEqual(context_post, new_post)

    def test_new_post_group_list(self):
        """
        Проверяет, что новый пост
        попадает на первую позицию group_list.
        """
        new_post = Post.objects.create(
            author=self.user,
            text='Тест группы',
            group=self.group,
        )
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        context_post = response.context.get('page_obj')[0]

        self.assertEqual(context_post, new_post)

    def test_new_post_profile(self):
        """
        Проверяет, что новый пост
        попадает на первую позицию profile.
        """
        new_post = Post.objects.create(
            author=self.user,
            text='Тест профиля',
            group=self.group,
        )
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
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

    def test_comment_post_detail(self):
        """
        Проверяет, что созданный комментарий
        появляется на странице post_detail.
        """
        new_comment = Comment.objects.create(
            text='Тестовый коммент',
            post=self.post,
            author=self.user
        )

        response = self.client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        context_comment = response.context['comments'][0]

        self.assertEqual(context_comment, new_comment)

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


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsImageContextTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='new')
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
        cls.group = Group.objects.create(
            title='Тестовая группа картинки',
            slug='test-slug-image',
            description='Описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Пост с картинкой',
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def check_post_atributes(self, post):
        """Метод для проверки атрибутов переданного поста с картинкой."""
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

    def test_index_image(self):
        """Проверяет, что картинка поста передаётся в context index."""
        response = self.client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]

        self.check_post_atributes(post)

    def test_profile_image(self):
        """Проверяет, что картинка поста передаётся в context profile."""
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        post = response.context['page_obj'][0]

        self.check_post_atributes(post)

    def test_group_list_image(self):
        """Проверяет, что картинка поста передаётся в context group_list."""
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        post = response.context['page_obj'][0]

        self.check_post_atributes(post)

    def test_post_detail_image(self):
        """Проверяет, что картинка поста передаётся в context post_detail."""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context['post']

        self.check_post_atributes(post)


class PostsFollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.follower = User.objects.create_user(username='follower')
        cls.follower_client = Client()
        cls.follower_client.force_login(cls.follower)
        cls.post = Post.objects.create(
            text='follow test',
            author=cls.author
        )

    def test_following_flag_on_follower(self):
        """
        Проверяет наличие флага following
        в context страницы profile после подписки,
        и отсутствие флага после отписки.
        """
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}))
        response = self.follower_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.author.username}))
        following = response.context.get('following')

        self.assertTrue(following)

        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author.username}))
        response = self.follower_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.author.username}))
        following = response.context.get('following')

        self.assertFalse(following)

    def test_following_post_exists(self):
        """
        Проверяет, что пост автора,
        на которого подписан юзер, появляется
        в context follow_index.
        """
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}))
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
                     text='пост группы № %s' % i)
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
