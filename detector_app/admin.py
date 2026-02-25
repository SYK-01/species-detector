from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib import admin
from .models import DetectionResult, SearchHistory


@admin.register(DetectionResult)
class DetectionResultAdmin(admin.ModelAdmin):
    list_display = ['species_name', 'confidence_percent', 'source', 'detected_at']
    list_filter = ['source']
    ordering = ['-detected_at']


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['query', 'results_count', 'searched_at']
    ordering = ['-searched_at']

