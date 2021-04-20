from typing import Any, Dict

from django.views.generic import TemplateView


class MainView(TemplateView):
    template_name = 'main.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        return super().get_context_data(**kwargs)
