from django.test import TestCase
from django.utils import timezone

from .models import Chore, Person


class MarkDoneTests(TestCase):
    def setUp(self):
        self.alice = Person.objects.create(name="Alice", order=0)
        self.bob = Person.objects.create(name="Bob", order=1)
        self.carol = Person.objects.create(name="Carol", order=2)

    def test_mark_done_records_last_done_at(self):
        chore = Chore.objects.create(name="Dishes", assigned_to=self.alice)
        self.assertIsNone(chore.last_done_at)

        before = timezone.now()
        chore.mark_done()
        after = timezone.now()

        self.assertIsNotNone(chore.last_done_at)
        self.assertGreaterEqual(chore.last_done_at, before)
        self.assertLessEqual(chore.last_done_at, after)

    def test_mark_done_advances_to_next_person(self):
        chore = Chore.objects.create(name="Dishes", assigned_to=self.alice)

        chore.mark_done()

        self.assertEqual(chore.assigned_to, self.bob)

    def test_mark_done_wraps_around_past_last_person(self):
        chore = Chore.objects.create(name="Dishes", assigned_to=self.carol)

        chore.mark_done()

        self.assertEqual(chore.assigned_to, self.alice)

    def test_mark_done_full_rotation_cycle(self):
        chore = Chore.objects.create(name="Dishes", assigned_to=self.alice)

        chore.mark_done()
        self.assertEqual(chore.assigned_to, self.bob)

        chore.mark_done()
        self.assertEqual(chore.assigned_to, self.carol)

        chore.mark_done()
        self.assertEqual(chore.assigned_to, self.alice)

    def test_mark_done_persists_changes(self):
        chore = Chore.objects.create(name="Dishes", assigned_to=self.alice)

        chore.mark_done()
        chore.refresh_from_db()

        self.assertEqual(chore.assigned_to, self.bob)
        self.assertIsNotNone(chore.last_done_at)

    def test_mark_done_with_no_people_leaves_assignment_unset(self):
        Person.objects.all().delete()
        chore = Chore.objects.create(name="Dishes", assigned_to=None)

        chore.mark_done()

        self.assertIsNone(chore.assigned_to)
        self.assertIsNotNone(chore.last_done_at)

    def test_mark_done_single_person_stays_assigned(self):
        Person.objects.exclude(pk=self.alice.pk).delete()
        chore = Chore.objects.create(name="Dishes", assigned_to=self.alice)

        chore.mark_done()
        self.assertEqual(chore.assigned_to, self.alice)

        chore.mark_done()
        self.assertEqual(chore.assigned_to, self.alice)

    def test_mark_done_with_unassigned_chore_assigns_first_person(self):
        chore = Chore.objects.create(name="Dishes", assigned_to=None)

        chore.mark_done()

        self.assertEqual(chore.assigned_to, self.alice)
