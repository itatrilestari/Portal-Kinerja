from decimal import Decimal
from django.db import models
from apps.api.models import TimeStampedUUIDModel, Log, WorkingUnit, Attachment
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

class PerformanceTargets(TimeStampedUUIDModel):
    working_unit = models.ForeignKey(WorkingUnit, null=True, blank=True, on_delete=models.CASCADE, related_name='performance_targets')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    year = models.IntegerField(null=True, blank=True)
    title = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50)
    logs = models.ManyToManyField(Log, blank=True, related_name="performance_targets")

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
    target = models.FloatField(blank=True, null=True)
    cascading_method = models.CharField(max_length=255, blank=True, null=True) # metode cascading
    unit = models.CharField(max_length=255, blank=True, null=True) # satuan
    type = models.CharField(max_length=255, blank=True, null=True)
    year = models.IntegerField(null=True, blank=True)
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

    def __str__(self):
        return self.category

    def _get_tw(self, *fields):
        """Helper: return Decimal values only if all fields are not None."""
        values = [getattr(self, f) for f in fields]
        if any(v is None for v in values):
            return None
        return [Decimal(v) for v in values]

    # Semester 1
    def semester_satu_rata_rata(self):
        #(Tw I + Tw II) / 2
        vals = self._get_tw('tw1', 'tw2')
        if vals is None:
            return None
        return sum(vals) / Decimal('2')

    def semester_satu_posisi_akhir(self):
        #Nilai Tw II
        return Decimal(self.tw2) if self.tw2 is not None else None

    def semester_satu_akumulasi(self):
        #Tw I + Tw II
        vals = self._get_tw('tw1', 'tw2')
        if vals is None:
            return None
        return sum(vals)

    # s.d. Triwulan 3
    def tw_tiga_rata_rata(self):
        #(Tw I + Tw II + Tw III) / 3
        vals = self._get_tw('tw1', 'tw2', 'tw3')
        if vals is None:
            return None
        return sum(vals) / Decimal('3')

    def tw_tiga_posisi_akhir(self):
        #Nilai Tw III
        return Decimal(self.tw3) if self.tw3 is not None else None

    def tw_tiga_akumulasi(self):
        #Tw I + Tw II + Tw III
        vals = self._get_tw('tw1', 'tw2', 'tw3')
        if vals is None:
            return None
        return sum(vals)

    # Semester 2
    def semester_dua_rata_rata(self):
        #(Tw I + Tw II + Tw III + Tw IV) / 4
        vals = self._get_tw('tw1', 'tw2', 'tw3', 'tw4')
        if vals is None:
            return None
        return sum(vals) / Decimal('4')

    def semester_dua_posisi_akhir(self):
        #Nilai Tw IV
        return Decimal(self.tw4) if self.tw4 is not None else None

    def semester_dua_akumulasi(self):
        #Tw I + Tw II + Tw III + Tw IV
        vals = self._get_tw('tw1', 'tw2', 'tw3', 'tw4')
        if vals is None:
            return None
        return sum(vals)

class PerformanceDocument(TimeStampedUUIDModel):
    unker = models.ForeignKey(WorkingUnit, on_delete=models.CASCADE, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    attachment = models.ManyToManyField(Attachment, blank=True, related_name="attachment")
    notes = models.TextField(blank=True, null=True)
    year = models.IntegerField(null=True, blank=True)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.unker.name} - {self.category}"
    
class Recommendation(TimeStampedUUIDModel):
    unker = models.ForeignKey(WorkingUnit, on_delete=models.CASCADE, blank=True, null=True)
    year = models.IntegerField(null=True, blank=True)
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