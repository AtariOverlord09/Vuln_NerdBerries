import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.test_posts_context import post_test_context
from posts.models import category, Post, Comment, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

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

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}): (
                'posts/create_post.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}): (
                'posts/post_detail.html'
            ),
            reverse('posts:category_list', kwargs={'slug': self.category.slug}): (
                'posts/category_list.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:profile', kwargs={'username': self.user}): (
                'posts/profile.html'
            ),
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        # --------------------------------------------------------
        # ТЕСТ КОНТЕКСТА


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsContextTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.second_user = User.objects.create_user(username='Ger')
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.category = category.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description',
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
            content_type='image/gif',
        )

        cls.post_second = Post.objects.create(
            text='Hi',
            author=cls.user,
            category=cls.category,
            image=uploaded,

        )

        cls.post = Post.objects.create(
            text='Халк крушить!!',
            author=cls.user,
            category=cls.category,
            image=uploaded,
        )

        form_data = {
            'text': 'Hi! Its Me!'
        }

        cls.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': cls.post.id}),
            data=form_data
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_context_for_index_page(self):
        """
        Тест контекста index
        """
        response = self.authorized_client.get(reverse('posts:index'))
        post_context = post_test_context(
            response,
            self.post.text,
            self.user.username,
            self.category.title,
            self.post.image,
        )
        for index_post_data, created_post_data in post_context.items():
            with self.subTest(index_post_data=index_post_data):
                self.assertEqual(created_post_data, index_post_data)

    def test_context_for_category_list_page(self):
        """
        Тест контекста category_list
        """
        response = self.authorized_client.get(reverse(
            'posts:category_list', kwargs={'slug': self.category.slug})
        )
        post_context = post_test_context(
            response,
            self.post.text,
            self.user.username,
            self.category.title,
            self.post.image,
        )
        for index_post_data, created_post_data in post_context.items():
            with self.subTest(index_post_data=index_post_data):
                self.assertEqual(created_post_data, index_post_data)

    def test_context_for_profile_page(self):
        """
        Тест контекста profile
        """
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))

        author_of_post = response.context['author']
        self.assertEqual(author_of_post, self.post.author)

        profile_posts = post_test_context(
            response,
            self.post.text,
            self.user.username,
            self.category.title,
            self.post.image,
        )
        for first_post_data, value in profile_posts.items():
            with self.subTest(first_post_data=first_post_data):
                self.assertEqual(value, first_post_data)

    def test_context_for_post_detail_page(self):
        """
        Тест контекста post_detail
        """
        response = (self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}
        )))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.user)
        self.assertEqual(
            response.context.get('post').category.slug, self.category.slug
        )
        self.assertEqual(response.context.get('post').image, self.post.image)

        author_of_post = response.context['user']
        self.assertEqual(author_of_post, self.user)

    def test_post_detail_context_comment(self):
        """
        Тест контекста комммента post_detail
        """
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            response.context.get('comments').get(),
            Comment.objects.filter(post=self.post.id).get()
        )

    def test_comment(self):
        """Отправленный коммент закрепляется за постом"""
        comment = Comment.objects.get(post=self.post.id)
        self.assertEqual(self.post.comments.get().text, comment.text)

    def test_for_post_create_page(self):
        """
        Тест контекста post_create
        """
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'category': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_for_post_edit_page(self):
        """
        Тест контекста post_edit
        """
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'category': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        check_post_edit = response.context['is_edit']
        self.assertEqual(check_post_edit, True)
        response = response.context.get('post')
        self.assertEqual(response.text, self.post.text)
        self.assertEqual(response.author, self.user)
        self.assertEqual(response.category.slug, self.category.slug)

    def test_cache_posts(self):
        """
        Тест корректности кэширования записей на странице index
        """

        response = self.authorized_client.get(reverse('posts:index')).content
        self.post_second.delete()

        response2 = self.authorized_client.get(reverse('posts:index')).content

        self.assertEqual(response, response2)

    def test_cache_clear(self):
        """Удаление кэша удаляет несуществующий пост из ленты"""

        response2 = self.authorized_client.get(reverse('posts:index')).content
        cache.clear()
        response3 = self.authorized_client.get(reverse('posts:index'))

        self.assertNotEqual(response2, response3)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.category = category.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description',
        )
        batch_size = 13
        posts = (Post(
            text='Test-text',
            author=cls.user,
            category=cls.category,
        ) for iters in range(13))
        batch = list(posts)
        Post.objects.bulk_create(batch, batch_size)

    def test_first_page_contains_ten_records_index(self):

        posts_pages = {
            reverse('posts:index'): 10,
            reverse('posts:category_list', kwargs={'slug': self.category.slug}): 10,
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ): 10,
        }

        for response_url, posts_count in posts_pages.items():
            with self.subTest(response_url=response_url):
                response = self.client.get(response_url)
                self.assertEqual(
                    len(response.context['page_obj']), posts_count
                )

    def test_second_page_contains_three_records(self):
        posts_pages = {
            reverse(
                'posts:index'
            ): 3,
            reverse(
                'posts:category_list', kwargs={'slug': self.category.slug}
            ): 3,
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ): 3,
        }

        for response_url, posts_count in posts_pages.items():
            with self.subTest(response_url=response_url):
                response = self.client.get(response_url, {'page': 2})
                self.assertEqual(
                    len(response.context['page_obj']), posts_count
                )


class PostscategoryTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

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

    def test_post_appears_on_index_category_list_profile(self):
        posts_pages = {
            reverse('posts:index'): self.post,
            reverse(
                'posts:category_list',
                kwargs={'slug': self.category.slug}
            ): self.post,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): self.post,
        }
        for url, post in posts_pages.items():
            with self.subTest(url=url):
                response = (
                    self.authorized_client.get(url).context['page_obj'][0]
                )
                self.assertEqual(response, post)


class PostFollowTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='Author')
        cls.follower = User.objects.create_user(username='Follower')

        cls.follower_client = Client()
        cls.follower_client.force_login(cls.follower)

        cls.nonfollower_client = Client()
        cls.nonfollower_client.force_login(cls.author)
        cls.post = Post.objects.create(
            author=PostFollowTests.author,
            text='Тестовый пт',
        )
        cls.second_user = User.objects.create_user(username='Foll')

        cls.second_author = Client()
        cls.second_author.force_login(cls.second_user)

        cls.follow = Follow.objects.create(
            user=cls.follower,
            author=cls.author
        )

    def setUp(self):
        cache.clear()

    def test_follow(self):
        """Лента подписчика содержит пост автора"""

        response = PostFollowTests.follower_client.get(
            reverse('posts:follow_index')
        )

        post_context = post_test_context(
            response,
            self.post.text,
            self.author.username,
        )
        for index_post_data, created_post_data in post_context.items():
            with self.subTest(index_post_data=index_post_data):
                self.assertEqual(created_post_data, index_post_data)

    def test_unfollow(self):
        """Лента неподписанного на автора юзера не содержит пост автора"""
        Follow.objects.filter(user=self.follower, author=self.author).delete()

        response = PostFollowTests.follower_client.get(reverse(
            'posts:follow_index'
        ))

        self.assertNotEqual(
            response.context['page_obj'].object_list, self.post
        )

    def test_follow_index(self):
        """Новая запись появляется в ленте подписчика"""

        response_follower = PostFollowTests.follower_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(
            len(response_follower.context['page_obj']),
            1
        )

    def test_following(self):
        """Юзер может подписаться на другого юзера"""
        Follow.objects.filter(user=self.follower, author=self.author).delete()

        before_following = Follow.objects.count()

        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )
        )
        after_following = Follow.objects.count()

        self.assertEqual(after_following, before_following + 1)
        follow = Follow.objects.latest('id')
        self.assertEqual(follow.author, self.author)
        self.assertEqual(follow.user, self.follower)

    def test_unfollowing(self):
        """Юзер может отписаться от другого юзера"""

        before_unfollowing = Follow.objects.count()

        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author}
        ))
        after_unfollowing = Follow.objects.count()
        self.assertEqual(before_unfollowing - 1, after_unfollowing)

        self.assertFalse(Follow.objects.filter(
            user=self.follower,
            author=self.author
        ))
