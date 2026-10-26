from django.contrib import admin

from .models import Exposure, Location, Plant, Diagnostic
# Register your models here.

admin.site.register(Exposure)
admin.site.register(Location)
admin.site.register(Plant)
admin.site.register(Diagnostic)