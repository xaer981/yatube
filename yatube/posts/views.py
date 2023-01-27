from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import create_page_obj


def check_author(func):
    """
    Проверяет является ли юзер автором поста.
    Если нет - перенаправляет на страницу просмотра поста.
    """
    def check_user(request, *args, **kwargs):
        post = get_object_or_404(Post, id=kwargs['post_id'])
        if request.user == post.author:
            return func(request, *args, **kwargs)

        return redirect('posts:post_detail', kwargs['post_id'])

    return check_user


def index(request):
    """
    Выводит по N (число из константы POSTS_LIMIT) последних постов из Post
    на страницу главной.
    """
    template = 'posts/index.html'
    posts = Post.objects.select_related('group')
    page_obj = create_page_obj(request, posts)
    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


def group_posts(request, slug):
    """
    Выводит по N (число из константы POSTS_LIMIT) последних постов из Post,
    опубликованных в конкретной группе (Group),
    на страницу группы.
    """
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = create_page_obj(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, template, context)


def profile(request, username):
    """
    Выводит по N (число из константы POSTS_LIMIT) последних постов из Post,
    опубликованных конкретным пользователем (username).
    """
    template = 'posts/profile.html'
    profile = get_object_or_404(User, username=username)
    posts = profile.posts.all()
    page_obj = create_page_obj(request, posts)
    following = (not request.user.is_anonymous
                 and Follow.objects.filter(user=request.user, author=profile)
                 .exists())
    context = {
        'following': following,
        'profile': profile,
        'page_obj': page_obj,
    }

    return render(request, template, context)


def post_detail(request, post_id):
    """
    Выводит один пост из Post, выбранный по post_id,
    а также комментарии к посту и форму написания комментариев.
    """
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    context = {
        'post': post,
        'comments': comments,
        'form': CommentForm(),
    }

    return render(request, template, context)


@login_required
def post_create(request):
    """
    Если метод запроса - POST, проверяет данные из формы и сохраняет в БД.
    В поле автора ставится пользователь из запроса.
    Если GET - выводит на страницу пустую форму.
    """
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()

        return redirect('posts:profile', username=request.user.username)

    return render(request, template, {'form': form})


@login_required
@check_author
def post_edit(request, post_id):
    """
    Если метод запроса - POST, проверяет данные из формы
    и сохраняет изменённый пост в БД.
    Если GET - выводит на страницу форму с данными поста из БД.
    """
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()

        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'form': form,
        'is_edit': True,
    }

    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Добавляет запись в Comment."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Выводит на страницу все посты авторов, на кого подписан юзер."""
    template = 'posts/follow.html'
    user = get_object_or_404(User, username=request.user.username)
    posts = Post.objects.filter(author__following__user=user)
    page_obj = create_page_obj(request, posts)
    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Добавляет запись в подписке в Follow."""
    author = get_object_or_404(User, username=username)
    already_followed = Follow.objects.filter(
        user=request.user, author=author).exists()
    if request.user != author and not already_followed:
        Follow(user=request.user, author=author).save()

    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Удаляет запись о подписке из Follow."""
    Follow.objects.filter(
        user=request.user, author__username=username).delete()

    return redirect('posts:profile', username=username)
