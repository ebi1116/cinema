from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Booking, Movie, Payment, Show


admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'is_staff', 'is_active')


class ShowInline(admin.TabularInline):
    model = Show
    extra = 1


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'language', 'genre', 'status', 'created_at')
    list_editable = ('status',)
    search_fields = ('title', 'language', 'genre')
    list_filter = ('language', 'genre', 'status', 'created_at')
    inlines = [ShowInline]


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ('id', 'movie_id', 'show_date', 'timing', 'status')
    list_editable = ('status',)
    search_fields = ('movie__id',)
    list_filter = ('status', 'show_date', 'timing')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'movie_id', 'show_id', 'show_date', 'show_time', 'seat_number', 'status', 'booked_at')
    search_fields = ('user__id', 'movie__id', 'show__id', 'seat_number')
    list_filter = ('status', 'booked_at')
    readonly_fields = ('booked_at', 'cancelled_at')

    @admin.display(description='Show Time', ordering='show__timing')
    def show_time(self, obj):
        return obj.show.timing.strftime('%I:%M %p') if obj.show and obj.show.timing else 'No time set'

    @admin.display(description='Show Date', ordering='show__show_date')
    def show_date(self, obj):
        return obj.show.show_date if obj.show else 'No date set'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_id', 'booking_id', 'amount', 'method', 'status', 'paid_at')
    search_fields = ('transaction_id', 'booking__id')
    list_filter = ('status', 'method', 'paid_at')
    readonly_fields = ('transaction_id', 'paid_at')

# Register your models here.
