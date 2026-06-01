from .views import get_customer


def customer(request):
    return {'customer_user': get_customer(request)}
