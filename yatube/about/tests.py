from django.test import Client, TestCase
from django.urls import reverse


class AboutUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_about_urls(self):
        """Проверяет доступность и шаблоны страниц about и tech."""
        urls_and_templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in urls_and_templates.items():
            with self.subTest(field=url):
                response = AboutUrlTests.guest_client.get(url)
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

    def test_pages_correct_template(self):
        """
        Проверяет правильность использования шаблонов
        для view приложения about.
        """
        templates_pages_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
