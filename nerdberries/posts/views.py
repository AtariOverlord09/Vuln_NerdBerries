from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.paginator import paginator
from posts.forms import CommentForm, PostForm
from posts.models import Category, Post, Comment, Follow


User = get_user_model()


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    page_number = request.GET.get('page')
    context = {
        'page_obj': paginator(posts, page_number),
    }
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


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posts_count = post.author.posts.count
    comment_form = CommentForm()
    post_comments = Comment.objects.filter(post=post_id)
    template = 'posts/post_detail.html'
    context = {
        'form': comment_form,
        'comments': post_comments,
        'posts_count': posts_count,
        'post': post,
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

    if not post.author == request.user:
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
