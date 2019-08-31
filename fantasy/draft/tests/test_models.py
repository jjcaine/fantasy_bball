from django.test import TestCase

from draft.models import Projection
from django.contrib.auth.models import User


class ProjectionModelTests(TestCase):

    def get_test_user(self, username='testuser'):
        return User.objects.create_user(username)

    def test_new_projection(self):
        u = User.objects.create_user('testuser')
        projection = Projection.new_projection(u)

        self.assertIsInstance(projection, Projection)
        self.assertEqual(u, projection.owner)

    def test_invalidate_owner_projections(self):
        user = self.get_test_user()
        Projection.new_projection(user)
        Projection.new_projection(user)

        Projection.invalidate_owner_projection(user)

        projections = Projection.objects.filter(owner=user)

        for projection in projections:
            self.assertFalse(projection.current_projection)