from django.db import models

class AnalysisResult(models.Model):
    extension_id = models.CharField(max_length=100)
    result_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'detector'