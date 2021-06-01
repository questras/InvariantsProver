from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import (
    Entity,
    Directory,
    File,
    SectionCategory,
    SectionStatus,
    SectionStatusData,
    FileSection,
    FileProvingResult
)
from .forms import (
    CreateDirectoryForm,
    CreateFileForm
)

User = get_user_model()


def create_dummy_user(n: int):
    """Create user for testing purposes with
    `n` identifier"""

    return User.objects.create_user(username=f'test{n}', password='test_password')


def login_user(test_case, user):
    test_case.client.login(username=user.username, password='test_password')


class EntityModelTests(TestCase):
    def test_correct_default_validity_flag(self):
        e = Entity.objects.create()
        self.assertEqual(e.validity_flag, True)


class DirectoryModelTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)
        self.directory = Directory.objects.create(
            name='test name',
            description='test description',
            owner=self.user,
        )

    def test_delete_by_user_sets_availability_to_false(self):
        # Before deletion availability flag is True.
        self.assertEqual(self.directory.availability_flag, True)

        self.directory.delete_by_user()
        self.assertEqual(self.directory.availability_flag, False)


class FileModelTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)
        self.file = File.objects.create(
            description='test',
            owner=self.user
        )

    def test_delete_by_user_sets_availability_to_false(self):
        self.assertEqual(self.file.availability_flag, True)

        self.file.delete_by_user()
        self.assertEqual(self.file.availability_flag, False)


class SectionCategoryModelTests(TestCase):
    def setUp(self) -> None:
        self.category = SectionCategory.objects.create(
            name='test-category'
        )

    def test_str_method_returns_category_name(self):
        self.assertEqual(str(self.category), self.category.name)


class SectionStatusModelTests(TestCase):
    def setUp(self) -> None:
        self.status = SectionStatus.objects.create(
            name='test-status'
        )

    def test_correct_str_method(self):
        self.assertEqual(
            str(self.status),
            'Section Status: test-status'
        )


class SectionStatusDataModelTests(TestCase):
    def setUp(self) -> None:
        self.status = SectionStatus.objects.create(
            name='test-status'
        )

    def test_section_status_data_is_correctly_created(self):
        data = SectionStatusData.objects.create(
            data='test-data',
            status=self.status
        )

        self.assertEqual(data.data, 'test-data')
        self.assertEqual(data.status.name, 'test-status')


class FileSectionModelTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)
        self.file = File.objects.create(
            owner=self.user,
            description='test-desc'
        )
        self.section = FileSection.objects.create(
            name='test-section',
            related_file=self.file,
            category=SectionCategory.objects.create(name='test-category'),
            status=SectionStatus.objects.create(name='test-status')
        )

    def test_section_is_deleted_when_related_file_is_deleted(self):
        # Right now, 1 file and 1 section.
        self.assertEqual(File.objects.all().count(), 1)
        self.assertEqual(FileSection.objects.all().count(), 1)

        self.file.delete()

        self.assertEqual(File.objects.all().count(), 0)
        self.assertEqual(FileSection.objects.all().count(), 0)


class FileProvingResultModelTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)
        self.file = File.objects.create(
            owner=self.user,
            description='test-desc'
        )
        self.proving = FileProvingResult.objects.create(
            data='test-data',
            related_file=self.file,
        )

    def test_proving_result_is_deleted_when_related_file_is_deleted(self):
        # Right now, 1 file and 1 section.
        self.assertEqual(File.objects.all().count(), 1)
        self.assertEqual(FileProvingResult.objects.all().count(), 1)

        self.file.delete()

        self.assertEqual(File.objects.all().count(), 0)
        self.assertEqual(FileProvingResult.objects.all().count(), 0)


class CreateDirectoryFormTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)
        self.directory = Directory.objects.create(
            name='test-directory',
            owner=self.user,
            parent_dir=None
        )

    def test_form_is_invalid_when_trying_to_create_existing_dir(self):
        """Form is invalid when user tries to create directory
        with the same name, user and parent_dir as already existing dir."""

        data = {
            'name': 'test-directory',
            'parent_dir': None
        }
        form = CreateDirectoryForm(data, user=self.user)
        self.assertEqual(form.is_valid(), False)


class CreateFileFormTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)

    def test_form_is_invalid_without_uploaded_file(self):
        data = {
            'description': 'test-description',
            'parent_dir': None
        }

        # No files are provided
        form = CreateFileForm(data)
        self.assertEqual(form.is_valid(), False)


class FileContentViewTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)

    def test_no_file_returns_404_code(self):
        login_user(self, self.user)

        url = reverse('file-content', args=(1,))
        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)


class CurrentFilesAndDirsViewTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)
        self.directory = Directory.objects.create(
            name='test-name',
            owner=self.user
        )
        self.file = File.objects.create(
            owner=self.user,
            uploaded_file='test-file.txt',
            parent_dir=self.directory
        )

    def test_request_without_arguments_returns_data_from_main_directory(self):
        login_user(self, self.user)

        url = reverse('current-files-and-dirs')
        r = self.client.get(url)

        self.assertEqual(r.status_code, 200)
        data = r.json()

        self.assertEqual(len(data['directories']), 1)
        directory = data['directories'][0]
        self.assertEqual(directory['id'], self.directory.id)
        self.assertEqual(directory['name'], self.directory.name)

        # File in setUp is not in main directory so it shouldn't be present here.
        self.assertEqual(len(data['files']), 0)


class MainViewTests(TestCase):
    def setUp(self) -> None:
        self.url = reverse('main')

    def test_not_logged_user_is_redirected(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)


class AddFileViewTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)
        self.url = reverse('create-file')

    def test_get_method_is_not_allowed(self):
        login_user(self, self.user)

        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 405)


class AddDirViewTests(TestCase):
    def setUp(self) -> None:
        self.url = reverse('create-directory')
        self.user = create_dummy_user(1)
        self.data = {
            'name': 'test',
            'description': 'test-desc'
        }

    def test_logged_user_can_add_directory(self):
        login_user(self, self.user)

        # No directories right now.
        self.assertEqual(Directory.objects.all().count(), 0)

        r = self.client.post(self.url, data=self.data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Directory.objects.all().count(), 1)


class DeleteDirectoryViewTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)
        self.directory = Directory.objects.create(
            name='test-directory-1',
            owner=self.user
        )

    def test_deleted_directory_has_availability_flag_set_to_false(self):
        login_user(self, self.user)
        url = reverse('delete-directory', args=(self.directory.id,))

        # Before deletion.
        self.assertEqual(Directory.objects.filter(availability_flag=True).count(), 1)
        self.assertEqual(Directory.objects.filter(availability_flag=False).count(), 0)

        self.client.post(url)

        # After deletion.
        self.assertEqual(Directory.objects.filter(availability_flag=True).count(), 0)
        self.assertEqual(Directory.objects.filter(availability_flag=False).count(), 1)


class DeleteFileViewTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)
        self.file = File.objects.create(
            owner=self.user
        )

    def test_deleted_file_has_availability_flag_set_to_false(self):
        login_user(self, self.user)
        url = reverse('delete-file', args=(self.file.id,))

        # Before deletion.
        self.assertEqual(File.objects.filter(availability_flag=True).count(), 1)
        self.assertEqual(File.objects.filter(availability_flag=False).count(), 0)

        self.client.post(url)

        # After deletion.
        self.assertEqual(File.objects.filter(availability_flag=True).count(), 0)
        self.assertEqual(File.objects.filter(availability_flag=False).count(), 1)


class ProveFileViewTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)

    def test_proving_non_existing_file_returns_404(self):
        login_user(self, self.user)
        url = reverse('prove-file', args=(1,))

        r = self.client.post(url)
        self.assertEqual(r.status_code, 404)

    def test_user_cannot_prove_somebody_else_file(self):
        user2 = create_dummy_user(2)
        not_owned_file = File.objects.create(owner=user2)
        url = reverse('prove-file', args=(not_owned_file.pk,))

        login_user(self, self.user)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 404)
