from django.core.paginator import Paginator

from .constants import POSTS_LIMIT


def create_page_obj(request, posts):
    """
    Принимает request и список постов(posts).
    Возвращает объект paginator,
    по N (число из константы POSTS_LIMIT) постов на страницу.
    """
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)
