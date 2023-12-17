from django.urls import path

from about.views import AboutAuthorView


app_name = 'about'

urlpatterns = [
    path('author/', AboutAuthorView.as_view(), name='author'),
]
