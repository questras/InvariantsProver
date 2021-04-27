from enum import Enum

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# TODO:
# doesnt have to be exactly like in task description
# check whether values in enums are the only ones available

class Directory(models.Model):
    """Directory - is an entity that holds files and 
    other directories."""

    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    creation_date = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    # False if the directory was deleted:
    availability_flag = models.BooleanField(default=True)
    validity_flag = models.BooleanField(default=True)
    parent_dir = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,   # In main directory if null=True
        blank=True
    )

    def __str__(self) -> str:
        return f'{self.name} (dir) by {self.owner.username}'


class File(models.Model):
    """File - is an entity that contains a source code, the source 
    code is divided into sections."""

    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    creation_date = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    # False if the file was deleted
    availability_flag = models.BooleanField(default=True)
    validity_flag = models.BooleanField(default=True)
    parent_dir = models.ForeignKey(
        Directory,
        on_delete=models.CASCADE,
        null=True,   # In main directory if null=True
        blank=True
    )
    file = models.FileField(upload_to='files')

    def __str__(self) -> str:
        return f'{self.name} (file) by {self.owner.username}'


class SectionCategory(models.Model):
    """Section category - is an entity that defines the type 
    of a section; category defines the way the file section 
    is handled by the application. Possible section categories 
    are: procedure, property, lemma, assertion, invariant, 
    precondition, postcondition"""

    class SectionCategoryEnum(Enum):
        PROCEDURE = 'procedure'
        PROPERTY = 'property'
        LEMMA = 'lemma'
        ASSERTION = 'assertion'
        INVARIANT = 'invariant'
        PRECONDITION = 'precondition'
        POSTCONDITION = 'postcondition'

    name = models.CharField(
        max_length=256,
        choices=[(tag, tag.value) for tag in SectionCategoryEnum]
    )
    creation_date = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.name}'


class SectionStatus(models.Model):
    """Section status - is an entity that defines the status
    of a section; example status' are: proved, invalid, 
    counterexample, unchecked."""

    class SectionStatusEnum(Enum):
        PROVED = 'proved'
        INVALID = 'invalid'
        COUNTEREXAMPLE = 'counterexample'
        UNCHECKED = 'unchecked'

    name = models.CharField(
        max_length=256,
        choices=[(tag, tag.value) for tag in SectionStatusEnum]
    )
    creation_date = models.DateTimeField(auto_now=True)
    validity_flag = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'Section Status: {self.name}'


class SectionStatusData(models.Model):
    """Section status - is an entity that defines data associated 
    with the section status, e.g. the counterexample content, 
    the name of the solver that proved validity (e.g. Z3, CVC4 etc.)."""

    data = models.TextField()
    creation_date = models.DateTimeField(auto_now=True)
    validity_flag = models.BooleanField(default=True)
    status = models.ForeignKey(SectionStatus, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'Status data to status: {self.status.name}'


class FileSection(models.Model):
    """File section - is an entity that contains a meaningful 
    piece of code within a file or comments; 
    some file sections may contain subsections."""

    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        help_text='File, to which section relates.'
    )
    name = models.CharField(max_length=256, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    creation_date = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(SectionCategory, on_delete=models.CASCADE)
    status = models.ForeignKey(SectionStatus, on_delete=models.CASCADE)
    validity_flag = models.BooleanField(default=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    # A section can be a subsection of some parent section.
    parent_section = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self) -> str:
        return f'Section {self.name}. Status: {self.status.name}'
