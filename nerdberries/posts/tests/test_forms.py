import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import category, Post, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.category = category.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description',
        )
        cls.second_category = category.objects.create(
            title='test-title-test',
            slug='test-slug-test',
            description='test-description-test',
        )
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user,
            category=cls.category,
        )
        cls.form = PostForm()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.second_uploaded = SimpleUploadedFile(
            name='not_small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_for_post_create_form(self):
        """
        валидная форма создаёт запись в бд
        """
        form_data = {
            'text': 'test-test',
            'category': self.category.id,
            'image': self.uploaded,
        }

        posts_count_before_adding = Post.objects.count()
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            Post.objects.count(), posts_count_before_adding + 1
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'auth'}
        ))
        latest_post = Post.objects.latest('id')
        self.assertEqual(latest_post.text, form_data['text'])
        self.assertEqual(latest_post.category.id, form_data['category'])
        self.assertEqual(latest_post.author, self.user)
        self.assertEqual(latest_post.image.name, 'posts/small.gif')

    def test_post_edit_form(self):
        """
        Тест форма post_id изменила редактируемый пост
        """
        post_id = self.post.id

        form_data = {
            'text': 'Привет! Я изменил текст этого поста! И даже группу!',
            'category': self.second_category.id,
            'image': self.second_uploaded,
        }
        self.auth_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
        )
        edited_post = Post.objects.get(id=self.post.id)
        expected_text = 'Привет! Я изменил текст этого поста! И даже группу!'
        expected_data = {
            edited_post.text: expected_text,
            edited_post.category.id: self.second_category.id,
            edited_post.image.name: 'posts/not_small.gif'
        }
        for post_data, expected_post_data in expected_data.items():
            with self.subTest(post_data=post_data):
                self.assertEqual(post_data, expected_post_data)

    def test_post_comment_form(self):
        form_data = {
            'text': 'Это коммент!',
        }
        self.auth_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data
        )

        expected_comment = Comment.objects.latest('id')

        self.assertEqual(form_data['text'], expected_comment.text)
        self.assertEqual(self.user, expected_comment.author)
        self.assertEqual(self.post.id, expected_comment.post.id)
