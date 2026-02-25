from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone


class DetectionResult(models.Model):
    species_name = models.CharField(max_length=200)
    confidence = models.FloatField()
    source = models.CharField(max_length=20, choices=[('camera', 'Cámara'), ('upload', 'Subida')], default='upload')
    detected_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-detected_at']

    def __str__(self):
        return f"{self.species_name} ({self.confidence_percent})"

    @property
    def confidence_percent(self):
        return f"{self.confidence * 100:.1f}%"


class SearchHistory(models.Model):
    query = models.CharField(max_length=300)
    results_count = models.IntegerField(default=0)
    searched_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-searched_at']

    def __str__(self):
        return f'"{self.query}" → {self.results_count} resultados'




