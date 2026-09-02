from django.contrib import admin

from .models import Chore, Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    list_editable = ("order",)
    ordering = ("order", "name")
    search_fields = ("name",)


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ("name", "assigned_to", "last_done_at")
    list_filter = ("assigned_to",)
    search_fields = ("name",)
