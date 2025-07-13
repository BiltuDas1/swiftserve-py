from django.urls import path
from . import views

urlpatterns = [
    path("response", views.file_response_handler),
    path("webhook", views.file_download_handler),
]
