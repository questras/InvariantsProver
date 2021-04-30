from typing import Any, Dict

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy, reverse

from .models import Directory, File
from .forms import CreateDirectoryForm, CreateFileForm


def get_file_content(file):
    file.open('r')
    content = file.read()
    file.close()

    return content


class MainView(TemplateView):
    template_name = 'main.html'

    def _get_current_object(self, cls, phrase):
        obj = None

        if self.request.user.is_authenticated and phrase in self.request.GET:
            pk = self.request.GET[phrase]
            try:
                obj = cls.objects.get(
                    pk=pk,
                    owner=self.request.user,
                    availability_flag=True
                )
            except cls.DoesNotExist:
                obj = None
            except ValueError:
                # Instead of ID, got something else.
                obj = None

        return obj

    def _get_current_objects(self, cls, parent_dir: Directory = None):
        result = None
        if self.request.user.is_authenticated:
            result = cls.objects.filter(
                parent_dir=parent_dir,
                owner=self.request.user,
                availability_flag=True
            )

        return result

    def get_current_file(self):
        return self._get_current_object(File, 'file')

    def get_current_directory(self):
        return self._get_current_object(Directory, 'dir')

    def get_directories_to_show(self, parent_dir: Directory = None):
        return self._get_current_objects(Directory, parent_dir=parent_dir)

    def get_files_to_show(self, parent_dir: Directory = None):
        return self._get_current_objects(File, parent_dir=parent_dir)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        current_directory = self.get_current_directory()
        current_file = self.get_current_file()
        directories = self.get_directories_to_show(current_directory)
        files = self.get_files_to_show(current_directory)

        if current_file:
            file_content = get_file_content(current_file.uploaded_file)
        else:
            file_content = None

        context = super().get_context_data(**kwargs)
        context['directories'] = directories
        context['files'] = files
        context['current_dir'] = current_directory
        context['current_file'] = current_file
        context['file_content'] = file_content

        return context


class FileBaseCreateView(CreateView):
    """Base class for create view for file-based objects
    like file or directory"""

    success_url = reverse_lazy('main')

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        # Available parent dirs are only those that are user's.
        form.fields['parent_dir'].queryset = \
            Directory.objects.filter(
                owner=self.request.user,
                availability_flag=True
        )

        return form

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.owner = self.request.user
        obj.save()

        return super().form_valid(form)


class CreateFileView(FileBaseCreateView):
    form_class = CreateFileForm
    model = File
    template_name = 'create_file.html'


class CreateDirectoryView(FileBaseCreateView):
    form_class = CreateDirectoryForm
    model = Directory
    template_name = 'create_directory.html'

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs['user'] = self.request.user

        return form_kwargs


def delete_directory_view(request, pk):
    directory = get_object_or_404(
        Directory,
        pk=pk,
        owner=request.user,
        availability_flag=True
    )

    if request.method == 'POST':
        directory.delete_by_user()
        return redirect(reverse('main'))

    context = {
        'directory': directory,
    }
    return render(request, 'delete_directory.html', context)


def delete_file_view(request, pk):
    file = get_object_or_404(
        File,
        pk=pk,
        owner=request.user,
        availability_flag=True
    )

    if request.method == 'POST':
        file.delete_by_user()
        return redirect(reverse('main'))

    context = {
        'file': file,
    }
    return render(request, 'delete_file.html', context)
