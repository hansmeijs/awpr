# Register your models here.
from django.contrib import admin

# PR2018-04-20
from .models import Examyear, Country

admin.site.register(Examyear)
admin.site.register(Country)