from django.db import models


class Person(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Position in the rotation sequence; lower goes first.",
    )

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Chore(models.Model):
    name = models.CharField(max_length=200)
    assigned_to = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chores",
    )
    last_done_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
