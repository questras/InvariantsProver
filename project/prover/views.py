from typing import Any, Dict

from django.views.generic import TemplateView

from .models import Directory, File


# TODO: style for go back button
class MainView(TemplateView):
    template_name = 'main.html'

    def get_current_directory(self):
        """Return current working directory specified by
        ID in url query string, or None if no directory specified or
        query string is incorrect"""

        directory = None
        if 'dir' in self.request.GET:
            try:
                directory = Directory.objects.get(pk=self.request.GET['dir'])
            except Directory.DoesNotExist:
                directory = None
            except ValueError:
                # Instead of ID, got something else.
                directory = None

        return directory

    def get_directories_to_show(self, parent_dir: Directory = None):
        """Get directories to show in view that are in given
        parent_dir or are in main directory, if parent_dir is None."""

        return Directory.objects.filter(parent_dir=parent_dir)

    def get_files_to_show(self, parent_dir: Directory = None):
        """Get files to show in view that are in given
        parent_dir or are in main directory, if parent_dir is None."""

        return File.objects.filter(parent_dir=parent_dir)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        current_directory = self.get_current_directory()
        directories = self.get_directories_to_show(current_directory)
        files = self.get_files_to_show(current_directory)

        context = super().get_context_data(**kwargs)
        context['directories'] = directories
        context['files'] = files
        context['current_dir'] = current_directory

        return context
