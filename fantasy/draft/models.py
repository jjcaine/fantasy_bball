from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import User


class Projection(models.Model):
    upload_date = models.DateTimeField(default=timezone.now)
    current_projection = models.BooleanField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    @classmethod
    def new_projection(cls, user):
        return

    def __str__(self):
        return self.owner.username