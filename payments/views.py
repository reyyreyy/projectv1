from django.shortcuts import render
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import redirect


# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY

def checkout(request):
    return render(request, 'payments/checkout.html')

def success_view(request):
    return render(request, 'payments/success.html')

def cancel_view(request):
    return render(request, 'payments/cancel.html')



stripe.api_key = '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'

@csrf_exempt
def create_checkout_session(request):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': 'Math Course Access'},
                'unit_amount': 5000,  # $50.00
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='http://127.0.0.1:8000/payments/success/',
        cancel_url='http://127.0.0.1:8000/payments/cancel/',
    )
    return redirect(session.url, code=303)

