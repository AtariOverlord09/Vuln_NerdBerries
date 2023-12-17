import os

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db import connection
from django.http import QueryDict, HttpResponse
from django.conf import settings

from core.paginator import paginator
from posts.forms import CommentForm, PostForm, SearchForm
from posts.models import Category, Post, Comment, Follow, Purchase


User = get_user_model()


def index(request):
    form = SearchForm(request.GET)
    posts = Post.objects.all()
    template = 'posts/index.html'
    context = {}

    if form.is_valid():
        query = form.cleaned_data.get('query')
        if query:
            sql_query = f"SELECT * FROM posts_post WHERE title LIKE '%{query}%' OR text LIKE '%{query}%'"
            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                columns = [col[0] for col in cursor.description]
                posts = [dict(zip(columns, row)) for row in cursor.fetchall()]

            context.update({'query': query, 'posts': posts})

    page_number = request.GET.get('page')
    page_obj = paginator(posts, page_number, 10)

    query_dict = QueryDict(mutable=True)
    query_dict.update(request.GET)
    query_dict.pop('page', None)

    context.update({
        'page_obj': page_obj,
        'form': form, 
        'pagination_query_params': query_dict.urlencode(),
    })

    return render(request, template, context)


def category_posts(request, slug):
    template = 'posts/category_list.html'
    category = get_object_or_404(Category, slug=slug)
    posts = category.posts.all()
    page_number = request.GET.get('page')
    context = {
        'category': category,
        'page_obj': paginator(posts, page_number),
    }
    return render(request, template, context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.all()
    page_number = request.GET.get('page')
    template = 'posts/profile.html'
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(author=user, user=request.user).exists():
            following = True


    context = {
        'following': following,
        'author': user,
        'page_obj': paginator(posts, page_number),
    }
    return render(request, template, context)

def get_image(request, filename):
    image_path = os.path.join(settings.MEDIA_ROOT, filename)
    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            return HttpResponse(image_data, content_type='image/jpeg')
    except FileNotFoundError:
        return HttpResponse(status=404)


def post_detail(request, post_id):
    user = request.user
    post = get_object_or_404(Post, id=post_id)
    posts_count = post.author.posts.count
    comment_form = CommentForm()
    post_comments = Comment.objects.filter(post=post_id)
    template = 'posts/post_detail.html'
    product_purchased = False

    if request.user.is_authenticated:
        if Purchase.objects.filter(
            user=user, 
            post=post,
        ).exists():
            product_purchased = True

    context = {
        'form': comment_form,
        'comments': post_comments,
        'posts_count': posts_count,
        'post': post,
        'product_purchased': product_purchased,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    context = {'form': form}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    from_user = request.GET.get('from_user')

    if from_user:
        from_user = post.author

    if not post.author == from_user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    form = PostForm(instance=post)
    context = {'form': form, 'is_edit': True, 'post': post}
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):

    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    page_number = request.GET.get('page')
    context = {
        'page_obj': paginator(posts, page_number),
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if author != user:
        Follow.objects.get_or_create(
            user=user,
            author=author
        )
    return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(author=author, user=request.user).exists():
        Follow.objects.get(user=request.user, author=author).delete()

    return redirect('posts:profile', username)

@login_required
def make_purchase(request, post_id):
    user = request.user
    post = get_object_or_404(Post, id=post_id)
    Purchase.objects.get_or_create(
        user=user,
        post=post,
        price=post.price,
    )
    return redirect('posts:post_detail', post_id)

@login_required
def return_purchase(request, post_id):
    user = request.user
    post = get_object_or_404(Post, id=post_id)
    if Purchase.objects.filter(post=post, user=user).exists():
        Purchase.objects.get(post=post, user=user).delete()

    return redirect('posts:post_detail', post_id)

@login_required
def purchases(request):
    user = request.user
    purchases = user.purchases.all()
    page_number = request.GET.get('page')
    status_param = request.GET.get('status')

    page_obj = paginator(purchases, page_number, 10)
    template = 'posts/purchases.html'
    context = {
        'page_obj': page_obj,
        'status_param': status_param,
    }
    return render(request, template, context)
