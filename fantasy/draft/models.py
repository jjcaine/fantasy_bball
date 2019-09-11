from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import User


class ScoringCategory(models.Model):
    category_name = models.CharField(max_length=50)
    category_abbreviation = models.CharField(max_length=5)
    weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.00)

    def __str__(self):
        return self.category_name

    @staticmethod
    def insert_standard_categories():
        standard_categories = [
            ('Adjusted Field Goal %', 'adjfg%', 1.00),
            ('Free Throw %', 'ft%', 1.00),
            ('Three Pointers Made', '3/g', 1.00),
            ('Three Point %', '3%', 1.00),
            ('Offensive Rebounds', 'or/g', 1.00),
            ('Defensive Rebounds', 'dr/g', 1.00),
            ('Assists', 'a/g', 1.00),
            ('Steals', 's/g', 1.00),
            ('Blocks', 'b/g', 1.00),
            ('Turnovers', 'to/g', -1.00),
            ('Points', 'p/g', 1.00)
        ]

        for category in standard_categories:
            ScoringCategory.objects.create(category_name=category[0],
                                           category_abbreviation=category[1],
                                           weight=category[2]
                                           )


class Draft(models.Model):
    draft_name = models.CharField(max_length=100)
    draft_owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    scoring_categories = models.ManyToManyField(ScoringCategory, blank=True)

    @classmethod
    def new_draft(cls, draft_name, owner):
        return Draft.objects.create(draft_name=draft_name, draft_owner=owner)

    def __str__(self):
        return self.draft_name


class Projection(models.Model):
    upload_date = models.DateTimeField(default=timezone.now)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    draft = models.ForeignKey(Draft, on_delete=models.CASCADE)

    @classmethod
    def new_projection(cls, owner, draft):
        projection = Projection.objects.create(draft=draft, owner=owner)
        projection.save()
        return projection

    def __str__(self):
        return self.owner.username


class ProjectionColumns(models.Model):
    column_name = models.CharField(max_length=10)
    projection = models.ForeignKey(Projection, on_delete=models.CASCADE)
    mapped_scoring_category = models.ForeignKey(ScoringCategory, blank=True, null=True, on_delete=models.CASCADE)
    informational = models.BooleanField(default=False, blank=True)
    discard = models.BooleanField(default=False, blank=True)