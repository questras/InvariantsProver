from django.contrib import admin

from .models import (
    Directory,
    File,
    SectionCategory,
    SectionStatusData,
    SectionStatus,
    FileSection
)


class AdminDirectory(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'parent_dir', 'availability_flag')


class AdminFile(admin.ModelAdmin):
    list_display = ('id', 'get_name', 'owner',
                    'parent_dir', 'availability_flag')


admin.site.register(Directory, AdminDirectory)
admin.site.register(File, AdminFile)
admin.site.register(SectionCategory)
admin.site.register(SectionStatusData)
admin.site.register(SectionStatus)
admin.site.register(FileSection)
