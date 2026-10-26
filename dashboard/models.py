from django.db import models
from accounts.models import User
# Create your models here.

class Exposure(models.Model):
    label = models.CharField("exposition", max_length=60)
    
    def __str__(self):
        return self.label
    
class Location(models.Model):
    label = models.CharField("localisation", max_length=60)
    
    def __str__(self):
        return self.label
    
class Plant(models.Model):
    name = models.CharField("nom", max_length=60)
    plant_type = models.CharField("type", max_length=60)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="plants")
    exposure = models.ForeignKey(Exposure, on_delete=models.PROTECT)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    
    def __str__(self):
        return self.name

class Diagnostic(models.Model):
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name="diagnostics")
    image = models.ImageField("image", upload_to="diagnostics/")
    result = models.CharField("résultat", max_length=100, blank=True)
    confidence = models.FloatField("confiance", null=True, blank=True)
    advice = models.TextField("conseils", blank=True)
    created_at = models.DateTimeField("date du diagnostic", auto_now_add=True)
    
    def __str__(self):
        return f"{self.plant.name} - {self.created_at:%d/%m/%Y}"
    