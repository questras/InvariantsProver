from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed

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


@login_required
def file_content_view(request, pk):
    file = get_object_or_404(
        File,
        pk=pk,
        owner=request.user,
        availability_flag=True
    )

    body = {
        'body': get_file_content(file.uploaded_file)
    }
    return JsonResponse(body, safe=False)


@login_required
def current_files_and_dirs_view(request):
    if current_directory_id := request.GET.get(key='dir', default=None):
        current_directory = get_object_or_404(Directory, pk=current_directory_id)
    else:
        current_directory = None

    directories = Directory.objects.filter(
        parent_dir=current_directory,
        owner=request.user,
        availability_flag=True
    )
    files = File.objects.filter(
        parent_dir=current_directory,
        owner=request.user,
        availability_flag=True
    )

    data = {
        'directories': list(directories.values('id', 'name')),
        'files': [{'id': f.id, 'name': f.get_name()} for f in files]
    }

    return JsonResponse(data, safe=False)


# todo: add login required mixin
class MainView(TemplateView):
    template_name = 'main.html'


# todo: add login required mixin
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


# todo: add login required mixin
class CreateFileView(FileBaseCreateView):
    form_class = CreateFileForm
    model = File
    template_name = 'create_file.html'


# todo: add login required mixin
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


@login_required
def delete_directory_view(request, pk):
    directory = get_object_or_404(
        Directory,
        pk=pk,
        owner=request.user,
        availability_flag=True
    )

    if request.method == 'POST':
        delete_directory_recurrent(directory)
        return HttpResponse()

    return HttpResponseNotAllowed(permitted_methods=['POST'])


@login_required
def delete_file_view(request, pk):
    file = get_object_or_404(
        File,
        pk=pk,
        owner=request.user,
        availability_flag=True
    )

    if request.method == 'POST':
        file.delete_by_user()
        return HttpResponse()

    return HttpResponseNotAllowed(permitted_methods=['POST'])


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
