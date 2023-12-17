from django.urls import path

from . import views


app_name = 'secret'

urlpatterns = [
    path('ping_site/', views.ping_site, name='ping_site')
]
