import csv
import uuid
from collections import defaultdict
from functools import wraps

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render

from .models import Booking, Movie, Payment, Show


SEAT_ROWS = ['A', 'B', 'C', 'D', 'E']
SEAT_NUMBERS = range(1, 11)
SEAT_PRICE = 180
CUSTOMER_SESSION_KEY = 'customer_user_id'


def get_customer(request):
    customer_id = request.session.get(CUSTOMER_SESSION_KEY)
    if not customer_id:
        return None
    try:
        return User.objects.get(pk=customer_id, is_staff=False, is_superuser=False, is_active=True)
    except User.DoesNotExist:
        request.session.pop(CUSTOMER_SESSION_KEY, None)
        return None


def customer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        customer = get_customer(request)
        if not customer:
            return redirect('login')
        request.customer = customer
        return view_func(request, *args, **kwargs)
    return wrapper


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


def home(request):
    movies = Movie.objects.filter(status=Movie.ACTIVE).prefetch_related('shows')
    return render(request, 'bookings/home.html', {'movies': movies})


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie.objects.filter(status=Movie.ACTIVE).prefetch_related('shows'), pk=movie_id)
    grouped_shows = defaultdict(list)
    for show in movie.shows.all():
        if show.status == Show.SCHEDULED:
            grouped_shows[show.show_date].append(show)

    show_groups = [
        {'date': show_date, 'shows': shows}
        for show_date, shows in sorted(grouped_shows.items())
    ]
    return render(request, 'bookings/movie_detail.html', {'movie': movie, 'show_groups': show_groups})


def signup_view(request):
    if get_customer(request):
        return redirect('home')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data['email']
        user.save()
        request.session[CUSTOMER_SESSION_KEY] = user.id
        messages.success(request, 'Welcome! Your account is ready.')
        return redirect('home')
    return render(request, 'bookings/auth_form.html', {'form': form, 'title': 'Create Account', 'button_label': 'Sign Up'})


def login_view(request):
    if get_customer(request):
        return redirect('home')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user.is_staff or user.is_superuser:
            form.add_error(None, 'Admin accounts must use the Admin login.')
        else:
            request.session[CUSTOMER_SESSION_KEY] = user.id
            return redirect(request.GET.get('next') or 'home')
    return render(request, 'bookings/auth_form.html', {'form': form, 'title': 'Login', 'button_label': 'Login'})


def logout_view(request):
    if CUSTOMER_SESSION_KEY in request.session:
        request.session.pop(CUSTOMER_SESSION_KEY, None)
    elif request.user.is_authenticated:
        logout(request)
    return redirect('home')


def export_database(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/admin/login/?next=/export-database/')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cine_database_export.csv"'

    writer = csv.writer(response)

    writer.writerow(['MOVIES'])
    writer.writerow(['id', 'title', 'language', 'genre', 'description', 'image', 'status', 'created_at'])
    for movie in Movie.objects.all().order_by('id'):
        writer.writerow([
            movie.id,
            movie.title,
            movie.language,
            movie.genre,
            movie.description,
            movie.image.name,
            movie.status,
            movie.created_at,
        ])

    writer.writerow([])
    writer.writerow(['SHOWS'])
    writer.writerow(['id', 'movie_id', 'show_date', 'timing', 'status'])
    for show in Show.objects.all().order_by('id'):
        writer.writerow([
            show.id,
            show.movie_id,
            show.show_date,
            show.timing,
            show.status,
        ])

    writer.writerow([])
    writer.writerow(['BOOKINGS'])
    writer.writerow(['id', 'user_id', 'movie_id', 'show_id', 'seat_number', 'status', 'booked_at', 'cancelled_at'])
    for booking in Booking.objects.all().order_by('id'):
        writer.writerow([
            booking.id,
            booking.user_id,
            booking.movie_id,
            booking.show_id,
            booking.seat_number,
            booking.status,
            booking.booked_at,
            booking.cancelled_at,
        ])

    writer.writerow([])
    writer.writerow(['PAYMENTS'])
    writer.writerow(['id', 'booking_id', 'amount', 'method', 'transaction_id', 'status', 'paid_at'])
    for payment in Payment.objects.all().order_by('id'):
        writer.writerow([
            payment.id,
            payment.booking_id,
            payment.amount,
            payment.method,
            payment.transaction_id,
            payment.status,
            payment.paid_at,
        ])

    writer.writerow([])
    writer.writerow(['USERS'])
    writer.writerow(['id', 'username', 'email', 'is_staff', 'is_active', 'date_joined'])
    for user in User.objects.all().order_by('id'):
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.is_staff,
            user.is_active,
            user.date_joined,
        ])

    return response


@customer_required
def seat_selection(request, show_id):
    show = get_object_or_404(Show.objects.select_related('movie'), pk=show_id, status=Show.SCHEDULED, movie__status=Movie.ACTIVE)
    booked_seats = set()
    for booking in Booking.objects.filter(show=show, status=Booking.CONFIRMED):
        booked_seats.update(booking.seats)

    seats = [
        [{'label': f'{row}{number}', 'booked': f'{row}{number}' in booked_seats} for number in SEAT_NUMBERS]
        for row in SEAT_ROWS
    ]

    if request.method == 'POST':
        selected_seats = [seat.strip() for seat in request.POST.getlist('seats') if seat.strip()]
        invalid_seats = [seat for seat in selected_seats if seat not in {f'{row}{number}' for row in SEAT_ROWS for number in SEAT_NUMBERS}]

        if not selected_seats:
            messages.error(request, 'Please select at least one seat.')
        elif invalid_seats:
            messages.error(request, 'Some selected seats are invalid.')
        else:
            with transaction.atomic():
                locked_bookings = Booking.objects.select_for_update().filter(show=show, status=Booking.CONFIRMED)
                unavailable = set()
                for booking in locked_bookings:
                    unavailable.update(booking.seats)

                duplicate_seats = unavailable.intersection(selected_seats)
                if duplicate_seats:
                    messages.error(request, f'Seats already booked: {", ".join(sorted(duplicate_seats))}')
                else:
                    request.session['pending_booking'] = {
                        'show_id': show.id,
                        'seats': selected_seats,
                    }
                    return redirect('payment')

    return render(request, 'bookings/seat_selection.html', {'show': show, 'seats': seats})


@customer_required
def payment(request):
    pending_booking = request.session.get('pending_booking')
    if not pending_booking:
        messages.error(request, 'Please select seats before payment.')
        return redirect('home')

    show = get_object_or_404(Show.objects.select_related('movie'), pk=pending_booking.get('show_id'), status=Show.SCHEDULED, movie__status=Movie.ACTIVE)
    selected_seats = pending_booking.get('seats', [])
    amount = len(selected_seats) * SEAT_PRICE

    if request.method == 'POST':
        method = request.POST.get('method', 'Dummy Card')
        with transaction.atomic():
            locked_bookings = Booking.objects.select_for_update().filter(show=show, status=Booking.CONFIRMED)
            unavailable = set()
            for booking in locked_bookings:
                unavailable.update(booking.seats)

            duplicate_seats = unavailable.intersection(selected_seats)
            if duplicate_seats:
                request.session.pop('pending_booking', None)
                messages.error(request, f'Seats already booked: {", ".join(sorted(duplicate_seats))}')
                return redirect('seat_selection', show_id=show.id)

            booking = Booking.objects.create(
                user=request.customer,
                movie=show.movie,
                show=show,
                seat_number=', '.join(selected_seats),
            )
            Payment.objects.create(
                booking=booking,
                amount=amount,
                method=method,
                transaction_id=f'TXN-{uuid.uuid4().hex[:12].upper()}',
            )

        request.session.pop('pending_booking', None)
        messages.success(request, 'Payment successful. Booking confirmed!')
        return redirect('home')

    return render(request, 'bookings/payment.html', {
        'show': show,
        'selected_seats': selected_seats,
        'seat_price': SEAT_PRICE,
        'amount': amount,
    })


@customer_required
def profile(request):
    bookings = Booking.objects.select_related('movie', 'show').prefetch_related('payment').filter(user=request.customer)
    return render(request, 'bookings/profile.html', {'bookings': bookings})


@customer_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.customer)
    if request.method != 'POST':
        return redirect('profile')

    if booking.status == Booking.CANCELLED:
        messages.info(request, 'This ticket is already cancelled.')
        return redirect('profile')

    booking.status = Booking.CANCELLED
    booking.cancelled_at = timezone.now()
    booking.save(update_fields=['status', 'cancelled_at'])

    if hasattr(booking, 'payment'):
        booking.payment.status = Payment.REFUNDED
        booking.payment.save(update_fields=['status'])

    messages.success(request, 'Ticket cancelled. The seats are now available again.')
    return redirect('profile')

# Create your views here.
