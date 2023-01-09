from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    """
    Форма создания/редактирования поста.
    Имеет три поля: текст(text), группа(group) и картинка(image).
    """
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']


class CommentForm(ModelForm):
    """Форма создания комментария. Имеет одно поле: текст(text)."""
    class Meta:
        model = Comment
        fields = ['text']
