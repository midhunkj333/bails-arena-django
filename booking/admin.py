from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Customer, Turf, Slot, Booking

admin.site.register(Customer)
admin.site.register(Turf)
admin.site.register(Slot)
admin.site.register(Booking)