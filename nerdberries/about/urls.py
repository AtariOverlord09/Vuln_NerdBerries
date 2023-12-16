from django.urls import path

from about.views import AboutAuthorView, TechnicalComponentView


app_name = 'about'

urlpatterns = [
    path('author/', AboutAuthorView.as_view(), name='author'),
    path('tech/', TechnicalComponentView.as_view(), name='tech'),
]
