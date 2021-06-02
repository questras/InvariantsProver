import os

from . import processes
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

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
from .views import (
    get_file_content,
    parse_error_message,
    delete_directory_recurrent
)

User = get_user_model()


def get_test_file_path() -> str:
    filename = 'testfile.txt'
    filepath = os.path.join(settings.BASE_DIR, 'files', 'tests', filename)
    return filepath


def create_dummy_file() -> str:
    """Create a file in {static}/files/tests/ directory
    for testing purposes."""

    filepath = get_test_file_path()

    f = open(filepath, 'w+')
    f.close()

    return filepath


def delete_dummy_file():
    """Delete a file create in `create_dummy_file`."""

    filepath = get_test_file_path()
    os.remove(filepath)


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

    def test_correct_str_method(self):
        want = 'test name'
        got = str(self.directory)
        self.assertEqual(got, want)


class FileModelTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)
        self.file = File.objects.create(
            description='test',
            owner=self.user,
            uploaded_file=create_dummy_file()
        )

    def tearDown(self) -> None:
        delete_dummy_file()

    def test_delete_by_user_sets_availability_to_false(self):
        self.assertEqual(self.file.availability_flag, True)

        self.file.delete_by_user()
        self.assertEqual(self.file.availability_flag, False)

    def test_get_name_gives_correct_filename(self):
        want = get_test_file_path().split('/')[-1]
        got = self.file.get_name()
        self.assertEqual(got, want)

    def test_correct_str_method(self):
        want = get_test_file_path().split('/')[-1]
        got = str(self.file)
        self.assertEqual(got, want)


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
        self.status_data = SectionStatusData.objects.create(
            data='test-data',
            status=self.status
        )

    def test_section_status_data_is_correctly_created(self):
        self.assertEqual(self.status_data.data, 'test-data')
        self.assertEqual(self.status_data.status.name, 'test-status')

    def test_correct_str_method(self):
        want = 'Status data to status: test-status'
        got = str(self.status_data)
        self.assertEqual(got, want)


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

    def test_correct_str_method(self):
        want = 'Section test-section. Status: test-status'
        got = str(self.section)
        self.assertEqual(got, want)


class FileProvingResultModelTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)
        self.file = File.objects.create(
            owner=self.user,
            description='test-desc',
            uploaded_file=create_dummy_file()
        )
        self.proving = FileProvingResult.objects.create(
            data='test-data',
            related_file=self.file,
        )

    def tearDown(self) -> None:
        delete_dummy_file()

    def test_proving_result_is_deleted_when_related_file_is_deleted(self):
        # Right now, 1 file and 1 section.
        self.assertEqual(File.objects.all().count(), 1)
        self.assertEqual(FileProvingResult.objects.all().count(), 1)

        self.file.delete()

        self.assertEqual(File.objects.all().count(), 0)
        self.assertEqual(FileProvingResult.objects.all().count(), 0)

    def test_correct_str_method(self):
        want = 'Result of ' + get_test_file_path().split('/')[-1]
        got = str(self.proving)
        self.assertEqual(got, want)


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

    def test_returns_correct_file_data(self):
        login_user(self, self.user)

        file = File.objects.create(
            owner=self.user,
            uploaded_file=create_dummy_file()
        )
        category = SectionCategory.objects.create(
            name='test-category'
        )
        status = SectionStatus.objects.create(
            name='test-status'
        )
        status_data = SectionStatusData.objects.create(
            data='test-status-data',
            status=status
        )
        section = FileSection.objects.create(
            name='test-section',
            category=category,
            status=status,
            related_file=file
        )
        proving_result = FileProvingResult.objects.create(
            related_file=file,
            data='test-proving-result'
        )

        want = {
            'name': get_test_file_path().split('/')[-1],
            'body': '',
            'sections': [
                {
                    'category': 'test-category',
                    'body': 'test-status-data',
                    'status': 'test-status'
                }
            ],
            'result': 'test-proving-result'
        }

        r = self.client.get(reverse('file-content', args=(file.pk,)))
        self.assertEqual(r.status_code, 200)

        got = r.json()
        self.assertEqual(got, want)

        delete_dummy_file()


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

    def test_return_404_when_specified_dir_doesnt_exist(self):
        login_user(self, self.user)

        non_existing_dir_id = self.directory.pk + 1
        url = reverse('current-files-and-dirs') + f'?dir={non_existing_dir_id}'

        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)


class MainViewTests(TestCase):
    def setUp(self) -> None:
        self.url = reverse('main')

    def test_not_logged_user_is_redirected(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)

    def test_logged_user_can_access(self):
        user = create_dummy_user(1)
        login_user(self, user)

        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)


class AddFileViewTests(TestCase):
    def setUp(self) -> None:
        self.user = create_dummy_user(1)
        self.url = reverse('create-file')

    def test_get_method_is_not_allowed(self):
        login_user(self, self.user)

        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 405)

    def test_cannot_create_file_with_empty_uploaded_file_field(self):
        login_user(self, self.user)
        data = {'uploaded_file': ''}

        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 400)


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

    def test_cannot_create_directory_with_empty_name(self):
        login_user(self, self.user)

        self.assertEqual(Directory.objects.all().count(), 0)

        self.data['name'] = ''
        r = self.client.post(self.url, self.data)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Directory.objects.all().count(), 0)

    def test_cannot_access_view_with_get_method(self):
        login_user(self, self.user)

        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 405)


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

    def test_cannot_access_view_with_get_method(self):
        login_user(self, self.user)
        url = reverse('delete-directory', args=(self.directory.id,))

        r = self.client.get(url)
        self.assertEqual(r.status_code, 405)


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

    def test_cannot_access_view_with_get_method(self):
        login_user(self, self.user)
        url = reverse('delete-file', args=(self.file.id,))

        r = self.client.get(url)
        self.assertEqual(r.status_code, 405)


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

    def test_user_can_prove_owned_file(self):
        login_user(self, self.user)

        file = File.objects.create(
            owner=self.user,
            uploaded_file=create_dummy_file()
        )

        url = reverse('prove-file', args=(file.pk,))
        r = self.client.post(url)
        self.assertEqual(r.status_code, 200)

        delete_dummy_file()


class ViewsUtilsTests(TestCase):
    def test_get_file_content_returns_correct_content(self):
        user = create_dummy_user(1)
        file = File.objects.create(
            description='test',
            owner=user,
            uploaded_file=create_dummy_file()
        )

        text = 'test file text\n'
        f = open(get_test_file_path(), 'w')
        f.write(text)
        f.close()

        got = get_file_content(file.uploaded_file)

        self.assertEqual(got, text)

        delete_dummy_file()

    def test_parse_error_message(self):
        error_message_json = {
            'field1': [{'message': 'error1'}],
            'field2': [{'message': 'error2'}]
        }
        want = 'error1 error2 '
        got = parse_error_message(error_message_json)
        self.assertEqual(got, want)

    def test_delete_directory_recurrent_correctly_deletes(self):
        user = create_dummy_user(1)

        top_dir = Directory.objects.create(name='top_dir', owner=user)
        inner_dir = Directory.objects.create(
            name='inner_dir',
            owner=user,
            parent_dir=top_dir
        )
        inner_file = File.objects.create(
            owner=user,
            parent_dir=top_dir
        )
        inner_inner_dir = Directory.objects.create(
            name='inner_inner_dir',
            owner=user,
            parent_dir=inner_dir
        )

        delete_directory_recurrent(top_dir)

        objs = [top_dir, inner_dir, inner_file, inner_inner_dir]
        for obj in objs:
            obj.refresh_from_db()
            self.assertEqual(obj.availability_flag, False)


class ProcessesTests(TestCase):
    def test_frama_section_correct_str_method(self):
        frama_section = processes.FramaSection(
            category='test-category',
            status='test-status',
            body='test-body'
        )
        want = 'Category: test-category\nStatus: test-status\ntest-body'
        got = str(frama_section)
        self.assertEqual(got, want)

    def test_correct_frama_print_command(self):
        test_filepath = 'test/filepath/file.txt'
        test_result_filepath = 'test/filepath/result.txt'
        want = ['frama-c', '-wp', '-wp-print', '-wp-log',
                'r:' + test_result_filepath, test_filepath]
        got = processes._frama_c_print_command(test_filepath, test_result_filepath)
        self.assertEqual(got, want)
