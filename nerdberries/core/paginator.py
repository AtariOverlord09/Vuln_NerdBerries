from django.conf import settings
from django.core.paginator import Paginator


def paginator(posts, page_number, elements_per_page=None):
    if elements_per_page is None:
        elements_per_page = settings.CONSTANTS['POSTS_TO_VIEW']
    """
    Функция-пагинатор, позволяющая соблюдать правила DRY во view-функциях.
    Принимает на вход:
    элементы для размещения на старнице;
    номер страницы;
    количество элементов на одной странице;
    На выход функция передаёт объект страницы.
    """
    pagination = Paginator(posts, elements_per_page)
    page_obj = pagination.get_page(page_number)
    return page_obj
