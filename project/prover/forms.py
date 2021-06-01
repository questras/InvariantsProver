from django.forms import ModelForm
from django.core.exceptions import ValidationError

from .models import Directory, File


class CreateDirectoryForm(ModelForm):
    class Meta:
        model = Directory
        fields = ('name', 'description', 'parent_dir')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        parent_dir = cleaned_data.get('parent_dir')

        # Check if there is an available directory with the same
        # name in the same place.
        try:
            _ = Directory.objects.get(
                name=name,
                parent_dir=parent_dir,
                owner=self.user,
                availability_flag=True
            )
            raise ValidationError('Such directory already exists.')
        except Directory.DoesNotExist:
            pass


class CreateFileForm(ModelForm):
    class Meta:
        model = File
        fields = ('description', 'parent_dir', 'uploaded_file')
