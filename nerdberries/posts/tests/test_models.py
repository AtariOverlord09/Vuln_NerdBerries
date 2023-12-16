from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import category, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.follower_user_client = Client()
        cls.follower_user_client.force_login(cls.user)

        cls.second_user = User.objects.create_user(username='Hi')
        cls.author_user_client = Client()
        cls.author_user_client.force_login(cls.second_user)

        cls.category = category.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост тестовый, поэтому мясо кушать можно...',
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'created': 'Дата создания',
            'author': 'Автор',
            'category': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'category': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_format = {
            self.category: self.category.title,
            self.post: self.post.text[:15],
        }

        for model, format in expected_format.items():
            with self.subTest(model=model):
                self.assertEqual(str(model), format)
