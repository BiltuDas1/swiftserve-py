from django.urls import path
from . import views

urlpatterns = [
  path('response', views.file_response_handler)
]