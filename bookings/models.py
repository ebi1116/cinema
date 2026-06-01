from datetime import time

from django.conf import settings
from django.db import models
from django.utils import timezone


class Movie(models.Model):
    id = models.BigAutoField(primary_key=True)
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]

    title = models.CharField(max_length=150)
    language = models.CharField(max_length=80, default='Hindi')
    genre = models.CharField(max_length=100, default='Drama')
    description = models.TextField()
    image = models.ImageField(upload_to='movie_posters/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Show(models.Model):
    id = models.BigAutoField(primary_key=True)
    SCHEDULED = 'SCHEDULED'
    CANCELLED = 'CANCELLED'
    COMPLETED = 'COMPLETED'
    STATUS_CHOICES = [
        (SCHEDULED, 'Scheduled'),
        (CANCELLED, 'Cancelled'),
        (COMPLETED, 'Completed'),
    ]
    TIME_CHOICES = [
        (time(9, 0), '9:00 AM'),
        (time(13, 0), '1:00 PM'),
        (time(16, 30), '4:30 PM'),
        (time(19, 0), '7:00 PM'),
        (time(22, 30), '10:30 PM'),
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='shows')
    show_date = models.DateField(default=timezone.localdate)
    timing = models.TimeField(choices=TIME_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SCHEDULED)

    class Meta:
        ordering = ['show_date', 'timing']

    def __str__(self):
        timing = self.timing.strftime('%I:%M %p') if self.timing else 'No time set'
        show_date = self.show_date.strftime('%d %b %Y') if self.show_date else 'No date set'
        return f'{self.movie.title} - {show_date} - {timing}'


class Booking(models.Model):
    id = models.BigAutoField(primary_key=True)
    CONFIRMED = 'CONFIRMED'
    CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='bookings')
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='bookings')
    seat_number = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=CONFIRMED)
    booked_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-booked_at']

    def __str__(self):
        return f'{self.user.username} - {self.movie.title} ({self.seat_number})'

    @property
    def seats(self):
        return [seat.strip() for seat in self.seat_number.split(',') if seat.strip()]

    @property
    def is_cancelled(self):
        return self.status == self.CANCELLED


class Payment(models.Model):
    id = models.BigAutoField(primary_key=True)
    SUCCESS = 'SUCCESS'
    REFUNDED = 'REFUNDED'
    STATUS_CHOICES = [
        (SUCCESS, 'Success'),
        (REFUNDED, 'Refunded'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    method = models.CharField(max_length=50, default='Dummy Card')
    transaction_id = models.CharField(max_length=40, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SUCCESS)
    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f'{self.transaction_id} - {self.booking.movie.title}'

# Create your models here.
