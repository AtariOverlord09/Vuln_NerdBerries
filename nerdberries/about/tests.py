from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticPagesURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_posts_reverse_correct_urls(self):
        """
        reverse выдаёт корректные url
        """
        reverse_response = {
            'about:author': '/about/author/',
            'about:tech': '/about/tech/',
        }

        for view_name, url in reverse_response.items():
            with self.subTest(view_name=view_name):
                self.assertEqual(reverse(view_name), url)

    def test_about_url_exists_at_desired_location(self):
        """
        Проверка доступности статик-страниц 'about'
        """
        response_status = {
            reverse('about:author'): HTTPStatus.OK,
            reverse('about:tech'): HTTPStatus.OK,
        }
        for address, status_code_ok in response_status.items():
            with self.subTest(status_code_ok=status_code_ok):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code_ok)

    def test_about_url_uses_correct_template(self):
        """
        Проверка корректных шаблонов 'about'
        """
        posts_template = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }
        for template, address in posts_template.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
