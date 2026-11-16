from django.db import models
from apps.api.models import TimeStampedUUIDModel, Log, WorkingUnit, Attachment
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

class PerformanceTargets(TimeStampedUUIDModel):
    working_unit = models.ForeignKey(WorkingUnit, null=True, blank=True, on_delete=models.CASCADE, related_name='performance_targets')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    year = models.IntegerField()
    title = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50)
    log = models.ForeignKey(Log, on_delete=models.SET_NULL, null=True, blank=True)
    perspective = models.TextField(blank=True, null=True)
    activity = models.TextField(blank=True, null=True)
    crosscutting = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

class PerformanceIndicators(TimeStampedUUIDModel):
    unker = models.ForeignKey(WorkingUnit, on_delete=models.CASCADE, blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name="children")
    performance_targets = models.ForeignKey(PerformanceTargets, on_delete=models.CASCADE, blank=True, null=True) # sasaran
    definition = models.TextField(blank=True, null=True)
    data_source = models.TextField(blank=True, null=True) # sumber data
    validity = models.CharField(max_length=255, blank=True, null=True) # tingkat validitas
    polarization = models.CharField(max_length=255, blank=True, null=True)
    lower_limit = models.FloatField(blank=True, null=True)
    upper_limit = models.FloatField(blank=True, null=True)
    perspective = models.CharField(max_length=255, blank=True, null=True)
    reference_indicator = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name="reference_by") # indikator atasan
    calculation_data = models.CharField(max_length=255, blank=True, null=True) # pola perhitungan/perhitungan data
    state = models.CharField(max_length=255, blank=True, null=True) 
    calculation_method = models.TextField(blank=True, null=True) # cara perhitungan
    calculation_method_detail = models.TextField(blank=True, null=True) # cara perhitungan detail
    period = models.CharField(max_length=255, blank=True, null=True) # periode pelaporan
    target = models.CharField(max_length=255, blank=True, null=True)
    cascading_method = models.CharField(max_length=255, blank=True, null=True) # metode cascading
    unit = models.CharField(max_length=255, blank=True, null=True) # satuan
    type = models.CharField(max_length=255, blank=True, null=True)
    year = models.CharField(max_length=255, blank=True, null=True)
    remaining_breakdown = models.CharField(max_length=255, blank=True, null=True) # sisa breakdown
    approver = ArrayField(models.CharField(max_length=50), blank=True, default=list)
    sequence = models.IntegerField(default=0)
    logs = models.ManyToManyField(Log, blank=True, null=True, related_name="logs_indicator")
    approved_state = models.CharField(max_length=255, default="On Progress", blank=True, null=True)
    cascading = ArrayField(models.CharField(max_length=50), blank=True, default=list)
    extra_attributes = models.JSONField(blank=True, null=True)
    is_priority = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class AchievementTarget(TimeStampedUUIDModel):
    indicator = models.ForeignKey(PerformanceIndicators, on_delete=models.CASCADE, related_name="indicator_achievement", blank=True, null=True)
    period = models.CharField(max_length=50, blank=True, null=True)
    year = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    tw1 = models.DecimalField(max_digits=30, decimal_places=4, null=True, blank=True)
    tw2 = models.DecimalField(max_digits=30, decimal_places=4, null=True, blank=True)
    tw3 = models.DecimalField(max_digits=30, decimal_places=4, null=True, blank=True)
    tw4 = models.DecimalField(max_digits=30, decimal_places=4, null=True, blank=True)

class PerformanceDocument(TimeStampedUUIDModel):
    unker = models.ForeignKey(WorkingUnit, on_delete=models.CASCADE, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    attachment = models.ManyToManyField(Attachment, blank=True, related_name="attachment")
    notes = models.TextField(blank=True, null=True)
    year = models.CharField(max_length=255, blank=True, null=True)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.unker.name} - {self.category}"
    
class Recommendation(TimeStampedUUIDModel):
    unker = models.ForeignKey(WorkingUnit, on_delete=models.CASCADE, blank=True, null=True)
    year = models.CharField(max_length=255, blank=True, null=True)
    instruction = models.TextField(blank=True, null=True)
    approver = ArrayField(models.CharField(max_length=255), blank=True, default=list)

    def __str__(self):
        return f"{self.year} - {self.instruction}"

class Resolution(TimeStampedUUIDModel):
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    url = models.TextField(blank=True, null=True)
    action = models.CharField(max_length=255, blank=True, null=True)
    verification_state = models.CharField(max_length=255, blank=True, null=True)
    logs = models.ManyToManyField(Log, blank=True, null=True, related_name="logs_resolution")
    extra_attributes = models.JSONField(blank=True, null=True)

class Guide(TimeStampedUUIDModel):
    title = models.CharField(max_length=255, blank=True, null=True)
    feature_name = models.CharField(max_length=255, blank=True, null=True)
    attachment = models.ManyToManyField(Attachment)