from django.shortcuts import redirect


def set_status_and_redirect(request, new_status):
    # Получаем текущий URL
    current_url = request.build_absolute_uri()

    # Разбиваем URL на части
    base_url, query_string = current_url.split('?', 1) if '?' in current_url else (current_url, '')

    # Разбиваем query string на параметры
    params = dict(p.split('=') for p in query_string.split('&')) if query_string else {}

    # Обновляем параметр 'status' новым значением
    params['status'] = new_status

    # Собираем обновленный query string
    updated_query_string = '&'.join([f'{key}={value}' for key, value in params.items()])

    # Собираем обновленный URL
    updated_url = f'{base_url}?{updated_query_string}' if updated_query_string else base_url

    # Перенаправляем пользователя на новый URL
    return redirect(updated_url)