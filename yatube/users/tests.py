import re

from django.contrib.auth.forms import UserCreationForm
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse

from .forms import User


class UsersUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user('test', 'test@test.com', 'pass')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_urls_for_unauthorized_users(self):
        """
        Проверяет доступность страниц для всех юзеров
        и использованные шаблоны.
        """
        urls_and_templates = {
            '/auth/signup/': 'users/signup.html',
            '/auth/logout/': 'users/logged_out.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
        }
        for url, template in urls_and_templates.items():
            with self.subTest(field=url):
                response = UsersUrlTests.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    200,
                    f'{url} не доступна'
                )
                self.assertTemplateUsed(
                    response,
                    template,
                    f'{url} использует неверный шаблон'
                )

    def test_urls_for_authorized_users(self):
        """
        Проверяет доступность страниц,
        предназначенных для авторизованных юзеров,
        авторизованным юзерам.
        """
        urls_and_templates = {
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
        }
        for url, template in urls_and_templates.items():
            with self.subTest(field=url):
                response = UsersUrlTests.authorized_client.get(url)
                self.assertEqual(
                    response.status_code,
                    200,
                    f'{url} не доступна'
                )
                self.assertTemplateUsed(
                    response,
                    template,
                    f'{url} использует неверный шаблон'
                )

    def test_unauthorized_users_to_authorized_funcs(self):
        """
        Проверяет перенаправление неавторизованных юзеров
        при попытке открыть страницы,
        доступные только авторизованным.
        """
        urls_and_redirects = {
            '/auth/password_change/': (
                '/auth/login/?next=/auth/password_change/'),
            '/auth/password_change/done/': (
                '/auth/login/?next=/auth/password_change/done/'),
        }
        for url, redirect in urls_and_redirects.items():
            with self.subTest(field=url):
                response = UsersUrlTests.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response,
                    redirect
                )

    def test_password_reset_confirm(self):
        """Проверяет функцию восстановления пароля."""
        def utils_extract_reset_tokens(full_url):
            """Достаёт токен и uidb64 из тела письма."""
            return re.findall(r"/([\w\-]+)",
                              re.search(r"^http\://.+$",
                                        full_url,
                                        flags=re.MULTILINE)[0])[3:5]

        response = self.guest_client.get(reverse('users:password_reset'))
        self.assertEqual(
            response.status_code,
            200,
            'Страница восстановления пароля недоступна')

        response = self.guest_client.post(reverse('users:password_reset'),
                                          {'email': 'test@test.com'},
                                          follow=True)
        self.assertEqual(len(mail.outbox), 1, 'EMAIL c ссылкой не отправлен')

        msg = mail.outbox[0]
        uidb64, token = utils_extract_reset_tokens(msg.body)

        response = self.guest_client.get(
            reverse('users:password_reset_confirm',
                    kwargs={'token': token, 'uidb64': uidb64}))
        self.assertEqual(
            response.status_code,
            302,
            'Переход по ссылке из письма работает неверно')

        response = self.guest_client.post(
            reverse('users:password_reset_confirm',
                    kwargs={'token': token, 'uidb64': uidb64}),
            {'new_password1': 'pass', 'new_password2': 'pass'})
        self.assertEqual(
            response.status_code,
            302,
            'Изменение пароля по ссылке работает неверно')


class UsersPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_pages_correct_template(self):
        """
        Проверяет правильность использования шаблонов
        для view приложения users.
        """
        templates_pages_names = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:logout'): 'users/logged_out.html',
            reverse('users:login'): 'users/login.html',
            reverse('users:password_reset'): 'users/password_reset_form.html',
            reverse(
                'users:password_reset_done'): 'users/password_reset_done.html',
            reverse(
                'users:password_reset_complete'): ('users/'
                                                   'password_reset_complete'
                                                   '.html'),
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_signup_show_correct_context(self):
        """
        Проверяет правильность передачи формы в контекст страницы signup.
        """
        response = self.authorized_client.get(reverse('users:signup'))
        form = response.context.get('form')
        self.assertIsInstance(form, UserCreationForm)


class UsersFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_signup_form(self):
        """Валидная форма в signup создаёт запись в User."""
        form_data = {
            'username': 'test',
            'password1': 'test-pass',
            'password2': 'test-pass',
        }

        users_count = User.objects.count()

        response = self.guest_client.post(reverse('users:signup'),
                                          data=form_data,
                                          follow=True)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(User.objects.filter(username=form_data['username']))
