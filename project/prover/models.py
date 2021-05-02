from enum import Enum
import os

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Entity(models.Model):
    """Base model for all entities in data model."""

    validity_flag = models.BooleanField(default=True)
    creation_date = models.DateTimeField(auto_now=True)


class Directory(Entity):
    """Directory - is an entity that holds files and 
    other directories."""

    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    # False if the directory was deleted:
    availability_flag = models.BooleanField(default=True)

    parent_dir = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,  # In main directory if null=True
        blank=True
    )

    def delete_by_user(self):
        """If a user deletes a directory it is not removed from database,
        its `availability_flag` changes."""

        self.availability_flag = False
        self.save()

    def __str__(self) -> str:
        return self.name


class File(Entity):
    """File - is an entity that contains a source code, the source 
    code is divided into sections."""

    description = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    # False if the file was deleted
    availability_flag = models.BooleanField(default=True)
    parent_dir = models.ForeignKey(
        Directory,
        on_delete=models.CASCADE,
        null=True,  # In main directory if null=True
        blank=True
    )
    uploaded_file = models.FileField(upload_to='files')

    def delete_by_user(self):
        """If a user deletes a file it is not removed from database,
        its `availability_flag` changes."""

        self.availability_flag = False
        self.save()

    def get_name(self) -> str:
        return os.path.basename(self.uploaded_file.name)

    def __str__(self) -> str:
        return self.get_name()


class SectionCategory(Entity):
    """Section category - is an entity that defines the type 
    of a section; category defines the way the file section 
    is handled by the application. Possible section categories 
    are: procedure, property, lemma, assertion, invariant, 
    precondition, postcondition"""

    name = models.CharField(
        max_length=256,
    )

    def __str__(self) -> str:
        return f'{self.name}'


class SectionStatus(Entity):
    """Section status - is an entity that defines the status
    of a section; example status' are: proved, invalid, 
    counterexample, unchecked."""

    name = models.CharField(
        max_length=256,
    )

    def __str__(self) -> str:
        return f'Section Status: {self.name}'


class SectionStatusData(Entity):
    """Section status - is an entity that defines data associated 
    with the section status, e.g. the counterexample content, 
    the name of the solver that proved validity (e.g. Z3, CVC4 etc.)."""

    data = models.TextField()
    status = models.ForeignKey(
        SectionStatus,
        on_delete=models.CASCADE,
        related_name='data_set'
    )

    def __str__(self) -> str:
        return f'Status data to status: {self.status.name}'


class FileSection(Entity):
    """File section - is an entity that contains a meaningful 
    piece of code within a file or comments; 
    some file sections may contain subsections."""

    related_file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        help_text='File, to which section relates.'
    )
    name = models.CharField(max_length=256, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(SectionCategory, on_delete=models.CASCADE)
    status = models.ForeignKey(SectionStatus, on_delete=models.CASCADE)
    # A section can be a subsection of some parent section.
    parent_section = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self) -> str:
        return f'Section {self.name}. Status: {self.status.name}'


class FileProvingResult(Entity):
    related_file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        help_text='File, to which result relates.',
    )
    data = models.TextField()

    def __str__(self) -> str:
        return f'Result of {self.related_file.uploaded_file.name}'
