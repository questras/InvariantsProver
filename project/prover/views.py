from typing import Any, Dict

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy, reverse

from .models import (
    Directory,
    File,
    FileSection,
    SectionStatusData,
    SectionCategory,
    SectionStatus,
    FileProvingResult
)
from .forms import CreateDirectoryForm, CreateFileForm
from .processes import get_frama_c_print


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

    def get_current_sections(self, file: File):
        return FileSection.objects.filter(related_file=file, validity_flag=True)

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
        sections = self.get_current_sections(current_file)

        if current_file:
            file_content = get_file_content(current_file.uploaded_file)

            proving_results = FileProvingResult.objects.filter(
                related_file=current_file,
                validity_flag=True
            )
            if len(proving_results) > 0:
                proving_result = proving_results[0]
            else:
                proving_result = None
        else:
            file_content = None
            proving_result = None

        context = super().get_context_data(**kwargs)
        context['directories'] = directories
        context['files'] = files
        context['current_dir'] = current_directory
        context['current_file'] = current_file
        context['file_content'] = file_content
        context['sections'] = sections
        context['proving_result'] = proving_result

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


def delete_directory_recurrent(directory: Directory):
    """Deletes (sets as unavailable) given directory and
    its contents recurrently."""

    for lower_directory in directory.directory_set.all():
        delete_directory_recurrent(lower_directory)

    for lower_file in directory.file_set.all():
        lower_file.delete_by_user()

    directory.delete_by_user()


def delete_directory_view(request, pk):
    directory = get_object_or_404(
        Directory,
        pk=pk,
        owner=request.user,
        availability_flag=True
    )

    if request.method == 'POST':
        delete_directory_recurrent(directory)
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


def prove_file_view(request, pk):
    file = get_object_or_404(
        File,
        pk=pk,
        owner=request.user,
        availability_flag=True
    )

    # Invalidate current sections and result.
    current_sections = FileSection.objects.filter(related_file=file, validity_flag=True)
    for section in current_sections:
        section.validity_flag = False
        section.save()
    current_results = FileProvingResult.objects.filter(related_file=file, validity_flag=True)
    for result in current_results:
        result.validity_flag = False
        result.save()

    # Start new validation process for current file.
    result_data, parsed_sections = get_frama_c_print(file.uploaded_file.path)
    for section in parsed_sections:
        s_category = SectionCategory.objects.create(name=section.category)
        s_status = SectionStatus.objects.create(name=section.status)
        SectionStatusData.objects.create(
            data=section.body,
            status=s_status
        )
        FileSection.objects.create(
            related_file=file,
            category=s_category,
            status=s_status
        )
    FileProvingResult.objects.create(
        related_file=file,
        data=result_data
    )

    parent_dir_pk = file.parent_dir.pk if file.parent_dir else ''
    return redirect(reverse('main') + f'?dir={parent_dir_pk}&file={file.pk}')
