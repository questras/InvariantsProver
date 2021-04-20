from django.contrib import admin

from .models import (
    Directory,
    File,
    SectionCategory,
    SectionStatusData,
    SectionStatus,
    FileSection
)

admin.site.register(Directory)
admin.site.register(File)
admin.site.register(SectionCategory)
admin.site.register(SectionStatusData)
admin.site.register(SectionStatus)
admin.site.register(FileSection)
