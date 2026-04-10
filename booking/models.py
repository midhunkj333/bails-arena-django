from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    is_frequent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Turf(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Slot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['start_time']  # ✅ ensures sorted slots

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"


# 🆕 GROUP BOOKINGS (for series + multi-slot tracking)
class BookingGroup(models.Model):
    REPEAT_CHOICES = [
        ('NONE', 'None'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE)

    repeat_type = models.CharField(max_length=10, choices=REPEAT_CHOICES, default='NONE')
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} - {self.repeat_type}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('BOOKED', 'Booked'),
        ('CANCELLED', 'Cancelled'),
    ]

    date = models.DateField()
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    # 🆕 link to group (optional)
    group = models.ForeignKey(
        BookingGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings"
    )

    amount = models.DecimalField(max_digits=8, decimal_places=2)

    # 🆕 better status handling
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='BOOKED')

    # 🆕 track cancellation reason (optional)
    cancel_reason = models.TextField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

    # 🆕 audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('date', 'slot', 'turf')  # ✅ unchanged
        indexes = [
            models.Index(fields=['date', 'turf']),
            models.Index(fields=['customer']),
        ]

    def __str__(self):
        return f"{self.date} {self.slot}"