
from django.db import models

class Garment(models.Model):
    CATEGORY_CHOICES = [
        ("TOP", "Top"), ("BOTTOM", "Bottom"), ("DRESS", "Dress"),
        ("OUTERWEAR", "Outerwear"), ("SHOES", "Shoes"), ("BAG", "Bag")
    ]
    FIT_CHOICES = [
        ("fitted","fitted"),("relaxed","relaxed"),
        ("oversized","oversized"),("tailored","tailored")
    ]

    name = models.CharField(max_length=120)
    category = models.CharField(max_length=12, choices=CATEGORY_CHOICES)
    color = models.CharField(max_length=40)
    fit = models.CharField(max_length=20, choices=FIT_CHOICES)
    formality = models.IntegerField(default=3)
    warmth = models.IntegerField(default=2)
    price = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    tags = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.name} ({self.color})"
