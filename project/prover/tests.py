from django.test import TestCase
from django.contrib.auth import get_user_model

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

User = get_user_model()


def create_dummy_user(n: int):
    """Create user for testing purposes with
    `n` identifier"""

    return User.objects.create_user(username=f'test{n}', password='test_password')


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
