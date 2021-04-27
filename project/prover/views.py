from typing import Any, Dict

from django.views.generic import TemplateView

from .models import Directory, File


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
                obj = cls.objects.get(pk=pk, owner=self.request.user)
            except cls.DoesNotExist:
                obj = None
            except ValueError:
                # Instead of ID, got something else.
                obj = None

        return obj

    def _get_current_objects(self, cls, parent_dir: Directory = None):
        result = None
        if self.request.user.is_authenticated:
            result = cls.objects.filter(parent_dir=parent_dir, owner=self.request.user)

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
            file_content = get_file_content(current_file.file)
        else:
            file_content = None

        context = super().get_context_data(**kwargs)
        context['directories'] = directories
        context['files'] = files
        context['current_dir'] = current_directory
        context['current_file'] = current_file
        context['file_content'] = file_content

        return context
