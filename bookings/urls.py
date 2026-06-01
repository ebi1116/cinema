from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('movies/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('shows/<int:show_id>/seats/', views.seat_selection, name='seat_selection'),
    path('payment/', views.payment, name='payment'),
    path('profile/', views.profile, name='profile'),
    path('export-database/', views.export_database, name='export_database'),
    path('bookings/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
]
