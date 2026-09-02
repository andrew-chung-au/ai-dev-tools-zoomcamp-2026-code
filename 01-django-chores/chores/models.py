from django.db import models
from django.utils import timezone


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

    def mark_done(self):
        """Record completion and rotate assignment to the next person.

        Simple round-robin over Person.order (with wraparound), no
        skip/unavailability support. If no people exist, only
        last_done_at is updated.
        """
        self.last_done_at = timezone.now()

        people = list(Person.objects.all())
        if people:
            try:
                current_index = people.index(self.assigned_to)
                next_index = (current_index + 1) % len(people)
            except ValueError:
                next_index = 0
            self.assigned_to = people[next_index]

        self.save()
