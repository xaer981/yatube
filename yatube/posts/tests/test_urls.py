from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostsUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='url_test')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_guest_users_url(self):
        """Проверяет доступность страниц всем юзерам."""
        urls = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{str(self.post.id)}/',
        ]
        for url in urls:
            with self.subTest(field=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    200,
                    f'{url} не работает'
                )

    def test_guest_users_templates(self):
        """
        Проверяет правильность использования шаблонов страниц,
        доступных всем юзерам.
        """
        urls_and_templates = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{str(self.post.id)}/': 'posts/post_detail.html',
        }
        for url, template in urls_and_templates.items():
            with self.subTest(field=url):
                response = self.client.get(url)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'{url} использует неверный шаблон'
                )

    def test_authorized_users_url(self):
        """
        Проверяет доступность создания поста авторизованному юзеру,
        редактирования поста - его автору.
        """
        urls = [
            f'/posts/{str(self.post.id)}/edit/',
            '/create/',
        ]
        for url in urls:
            with self.subTest(field=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code,
                    200,
                    f'{url} не доступна'
                )

    def test_authorized_users_templates(self):
        """
        Проверяет правильность использования шаблонов страниц,
        доступных авторизованным юзерам (или только автору поста).
        """
        urls_and_templates = {
            f'/posts/{str(self.post.id)}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in urls_and_templates.items():
            with self.subTest(field=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'{url} использует неверный шаблон'
                )

    def test_unauthorized_users_to_authorized_funcs(self):
        """
        Проверяет перенаправление неавторизованных юзеров
        при попытке открыть страницы,
        доступные только авторизованным (или только автору поста).
        """
        urls_and_redirects = {
            f'/posts/{str(self.post.id)}/edit/': (
                reverse('users:login')
                + '?next='
                + reverse('posts:post_edit',
                          kwargs={'post_id': self.post.id})),
            '/create/': (
                reverse('users:login')
                + '?next='
                + reverse('posts:post_create')),
        }
        for url, redirect in urls_and_redirects.items():
            with self.subTest(field=url):
                response = self.client.get(url, follow=True)
                self.assertRedirects(
                    response,
                    redirect
                )

    def test_notauthor_edit_post(self):
        """
        Проверяет, что авторизованный юзер, не являющийся автором,
        при открытии post_edit перенаправляется на post_detail.
        """
        new_user = User.objects.create_user(username='new')
        new_post = Post.objects.create(
            author=new_user,
            text='новый пост',
        )
        response = self.authorized_client.get(
            f'/posts/{str(new_post.id)}/edit/')
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': new_post.id}))

    def test_authorized_users_comment(self):
        """
        Проверяет, что авторизованный юзер, при открытии add_comment,
        направляется на страницу просмотра поста.
        """
        response = self.authorized_client.get(
            f'/posts/{str(self.post.id)}/comment/')

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))

    def test_unauthorized_users_comment(self):
        """
        Проверяет, что неавторизованный юзер,
        при открытии add_comment, направляется на страницу login.
        """
        response = self.client.get(
            f'/posts/{str(self.post.id)}/comment/')

        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse(
                'posts:add_comment', kwargs={'post_id': self.post.id}))

    def test_authorized_users_follow(self):
        """
        Проверят, что авторизованный пользователь
        после успешной подписки на автора (profile_follow),
        направляется на его profile.
        """
        new_user = User.objects.create_user(username='follower')
        new_client = Client()
        new_client.force_login(new_user)
        urls_and_redirects = {
            f'/profile/{self.user.username}/follow/': (
                reverse('posts:profile',
                        kwargs={'username': self.user.username})),
            f'/profile/{self.user.username}/unfollow/': (
                reverse('posts:profile',
                        kwargs={'username': self.user.username}))
        }

        for url, redirect in urls_and_redirects.items():
            with self.subTest(field=url):
                response = new_client.get(url, follow=True)
                self.assertRedirects(
                    response,
                    redirect
                )

    def test_404(self):
        """Проверяет, что несуществующая страница возвращает ошибку 404."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(
            response.status_code,
            404,
            'Несуществующая страница не возвращает ошибку 404'
        )
