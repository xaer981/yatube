from django.test import TestCase


class TestErrors(TestCase):
    def test_404(self):
        """Проверяет правильность работы кастомной страницы 404."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')
