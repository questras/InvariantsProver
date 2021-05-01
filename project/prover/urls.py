from django.urls import path

from .views import (
    MainView,
    CreateDirectoryView,
    CreateFileView,
    delete_directory_view,
    delete_file_view,
    prove_file_view,
)

urlpatterns = [
    path('', MainView.as_view(), name='main'),
    path('create_dir/', CreateDirectoryView.as_view(), name='create-directory'),
    path('create_file/', CreateFileView.as_view(), name='create-file'),
    path('delete_dir/<int:pk>/', delete_directory_view, name='delete-directory'),
    path('delete_file/<int:pk>/', delete_file_view, name='delete-file'),
    path('prove/<int:pk>/', prove_file_view, name='prove-file'),
]
