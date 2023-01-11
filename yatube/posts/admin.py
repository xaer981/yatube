from django.contrib import admin

from .models import Comment, Follow, Group, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Отображает в админке поля модели Post,
    позволяет искать по тексту, фильтровать по дате публикации,
    изменять группу поста.
    """
    list_display = ('pk', 'text', 'created', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Отображает в админке поля модели Comment,
    позволяет искать по тексту, фильтровать по дате публикации.
    """
    list_display = ('pk', 'text', 'created', 'post', 'author')
    search_fields = ('text',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'


admin.site.register(Follow)
admin.site.register(Group)
