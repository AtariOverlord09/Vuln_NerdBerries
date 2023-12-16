from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import category, Post


User = get_user_model()


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user = User.objects.create_user(username='Author')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.user_not_author = User.objects.create_user(username='NotAuthor')
        cls.authorized_client_not_author = Client()
        cls.authorized_client_not_author.force_login(cls.user_not_author)

        cls.category = category.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description',
        )

        cls.post = Post.objects.create(
            text='Халк крушить!!',
            author=cls.user,
            category=cls.category,
        )

    def setUp(self):
        self.reverse_response = {
            # Индекс[0]
            reverse('posts:index'): '/',
            # Индекс POST_EDIT
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}): (
                f'/posts/{self.post.id}/edit/'
            ),
            # Индекс[3]
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}): (
                f'/posts/{self.post.id}/'
            ),
            # Индекс category_LIST
            reverse('posts:category_list', kwargs={'slug': self.category.slug}): (
                f'/category/{self.category.slug}/'
            ),
            # Индекс[4]
            reverse('posts:profile', kwargs={
                'username': self.user.username}
            ): (
                f'/profile/{self.user.username}/'
            ),
            # Индекс[6]
            reverse('posts:post_create'): '/create/',
            reverse('posts:add_comment', kwargs={
                'post_id': self.post.id
            }
            ): f'/posts/{self.post.id}/comment/'
        }
        self.reversed_url = list(self.reverse_response.keys())

        self.index = self.reversed_url[0]
        self.post_edit = self.reversed_url[1]
        self.post_detail = self.reversed_url[2]
        self.category_list = self.reversed_url[3]
        self.profile = self.reversed_url[4]
        self.post_create = self.reversed_url[5]
        self.comment = self.reversed_url[6]

    # ---------------------------------------------------------
    # Начало тестов на доступность к страницам приложения posts
    # ---------------------------------------------------------

    def test_posts_reverse_correct_urls(self):
        """
        reverse выдаёт корректные url
        """
        for reversed_url, url in self.reverse_response.items():
            with self.subTest(reversed_url=reversed_url):
                response = self.authorized_client.get(reversed_url)
                self.assertEqual(response.request['PATH_INFO'], url)

    def test_posts_url_exists_at_desired_location(self):
        """
        Проверка доступности общедоступных страниц приложения posts
        """

        reverse_status = {
            self.index: HTTPStatus.OK,
            self.category_list: HTTPStatus.OK,
            self.profile: HTTPStatus.OK,
            self.post_detail: HTTPStatus.OK,
        }
        for urls, status_code_ok in reverse_status.items():
            with self.subTest(urls=urls):
                response = self.guest_client.get(urls)
                self.assertEqual(response.status_code, status_code_ok)

    def test_post_url_create_for_auth_client(self):
        """
        Проверка доступа страницы create для авторизованного пользователя
        """
        response = self.authorized_client.get(
            self.post_create
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_url_create_for_guest_client(self):
        """
        Проверка доступа страницы create для гостевого клиента
        """
        response = self.guest_client.get(
            self.post_create, follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_page(self):
        """
        Проверка доступа автора поста к странице edit
        """
        response = self.authorized_client.get(
            self.post_edit
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_page_anonim(self):
        """
        Проверка редиректа из страницы edit для гостевого клиента
        """
        response = self.guest_client.get(
            self.post_edit
        )
        login_url = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        self.assertRedirects(response, login_url)

    def test_edit_page_for_not_author(self):
        """
        Проверка редиректа из страницы редактирования для не автора поста
        """
        response = self.authorized_client_not_author.get(
            self.post_edit
        )
        self.assertRedirects(
            response, self.post_detail
        )

    def test_post_comment_for_auth_user(self):
        """
        Проверка доступа к написанию комментария для авторизованного юзера
        """
        response = self.authorized_client.get(self.comment)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_comment_for_auth_user(self):
        """
        Проверка доступа к написанию комментария для неавторизованного юзера
        """
        response = self.guest_client.get(self.comment)
        login_url = f'/auth/login/?next=/posts/{self.post.id}/comment/'
        self.assertRedirects(response, login_url)

    def test_correct_url_for_unexisting_page(self):
        """
        Проверка правильного отображения по несуществующему url
        """
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    # --------------------------------------------------------
    # Конец тестов на доступность к страницам приложения posts
    # --------------------------------------------------------

    # --------------------------------------------------
    # Начало тестов по корректности отображения шаблонов
    # по соответствующему url
    # --------------------------------------------------

    def test_posts_url_uses_correct_template(self):
        """
        Проверка корректных общедоступных шаблонов страниц приложения post
        """
        posts_template = {
            self.index: 'posts/index.html',
            self.post_detail: (
                'posts/post_detail.html'
            ),
            self.category_list: (
                'posts/category_list.html'
            ),
            self.profile: 'posts/profile.html',
        }
        for address, template in posts_template.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_posts_url_uses_correct_template_for_auth_user(self):
        """
        Проверка отображения шаблона /create/ для авторизованного пользователя
        """
        response = self.authorized_client.get(
            self.post_create
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_posts_url_create_page_for_guest(self):
        """
        Проверка корректного отображения шаблона /create/ для гостевого клиента
        """
        response = self.guest_client.get(
            self.post_create
        )
        self.assertTemplateNotUsed(response, 'posts/create_post.html')

    def test_posts_url_edit_page_for_author(self):
        """
        Проверка отображения шаблона /posts/1/edit/ для автора поста
        """
        response = self.authorized_client.get(
            self.post_edit
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_posts_url_edit_page_for_author(self):
        """
        Проверка корректного отображения шаблона /posts/1/edit/ для не автора
        """
        response = self.authorized_client_not_author.get(
            self.post_edit
        )
        self.assertTemplateNotUsed(response, 'posts/create_post.html')

    def test_post_url_edit_page_for_guest(self):
        """
        Проверка отображения шаблона /posts/1/edit/ для гостевого клиента
        """
        response = self.guest_client.get(
            self.post_edit
        )
        self.assertTemplateNotUsed(response, 'posts/create_post.html')

    # -------------------------------------------------
    # Конец тестов по корректности отображения шаблонов
    # по соответствующему url
    # -------------------------------------------------
