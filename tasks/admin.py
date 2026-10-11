from django.contrib import admin

# Register your models here.
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'user',
        'priority',
        'status',
        'due_date',
    )

    list_filter = ('priority', 'status')
    search_fields = ('title', 'description')
