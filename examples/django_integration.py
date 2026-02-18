"""
Django integration example for EasyTrans SDK.

Shows how to integrate the SDK into a Django project.
"""

# ==========================================
# settings.py
# ==========================================

import os

EASYTRANS = {
    "SERVER_URL": "mytrans.nl",
    "ENVIRONMENT": os.environ.get("EASYTRANS_ENV", "demo"),
    "USERNAME": os.environ["EASYTRANS_USERNAME"],
    "PASSWORD": os.environ["EASYTRANS_PASSWORD"],
    "DEFAULT_MODE": "effect" if os.environ.get("ENVIRONMENT") == "production" else "test",
    "WEBHOOK_API_KEY": os.environ["EASYTRANS_WEBHOOK_KEY"],
}

# ==========================================
# services/easytrans_service.py
# ==========================================

from django.conf import settings
from easytrans import EasyTransClient, Order, Destination, Package
from easytrans.constants import CollectDeliver


def get_easytrans_client():
    """Factory function to create configured EasyTrans client."""
    return EasyTransClient(
        server_url=settings.EASYTRANS["SERVER_URL"],
        environment_name=settings.EASYTRANS["ENVIRONMENT"],
        username=settings.EASYTRANS["USERNAME"],
        password=settings.EASYTRANS["PASSWORD"],
        default_mode=settings.EASYTRANS["DEFAULT_MODE"],
    )


def create_shipment_from_order(order_model):
    """
    Create shipment in EasyTrans from Django order model.
    
    Args:
        order_model: Your Django Order model instance
    
    Returns:
        OrderResult from EasyTrans
    """
    client = get_easytrans_client()
    
    # Build destinations from your database
    pickup = Destination(
        collect_deliver=CollectDeliver.PICKUP.value,
        company_name=order_model.sender_company,
        address=order_model.sender_address,
        houseno=order_model.sender_house_number,
        postal_code=order_model.sender_postal_code,
        city=order_model.sender_city,
        country=order_model.sender_country,
    )
    
    delivery = Destination(
        collect_deliver=CollectDeliver.DELIVERY.value,
        company_name=order_model.receiver_company,
        address=order_model.receiver_address,
        houseno=order_model.receiver_house_number,
        postal_code=order_model.receiver_postal_code,
        city=order_model.receiver_city,
        country=order_model.receiver_country,
        customer_reference=order_model.order_number,
    )
    
    # Build packages
    packages = []
    for item in order_model.items.all():
        packages.append(Package(
            amount=float(item.quantity),
            weight=float(item.weight_kg),
            description=item.description,
        ))
    
    # Create order
    easytrans_order = Order(
        productno=2,  # Your EasyTrans product number
        date=order_model.ship_date.strftime("%Y-%m-%d"),
        external_id=str(order_model.id),  # Link back to Django model
        order_destinations=[pickup, delivery],
        order_packages=packages,
    )
    
    # Submit to EasyTrans
    result = client.import_orders([easytrans_order], mode="effect")
    
    # Save tracking info back to Django model
    if result.new_ordernos:
        order_model.easytrans_order_no = result.new_ordernos[0]
        tracking = result.order_tracktrace[str(result.new_ordernos[0])]
        order_model.tracking_number = tracking.local_trackingnr
        order_model.tracking_url = tracking.local_tracktrace_url
        order_model.save()
    
    return result


# ==========================================
# views.py - Webhook Handler
# ==========================================

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from easytrans import EasyTransClient
from easytrans.exceptions import EasyTransError
from .models import Order


@csrf_exempt
def easytrans_webhook(request):
    """
    Handle webhook callbacks from EasyTrans.
    
    Register this endpoint with EasyTrans:
    POST /api/easytrans/webhook/
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        # Parse and validate webhook
        webhook = EasyTransClient.parse_webhook(
            payload=request.body,
            expected_api_key=settings.EASYTRANS["WEBHOOK_API_KEY"],
            headers=dict(request.headers),
        )
        
        # Find order by external_id
        if webhook.order.externalId:
            try:
                order = Order.objects.get(id=webhook.order.externalId)
                
                # Update order status based on webhook
                if webhook.order.status == "collected":
                    order.status = "in_transit"
                    order.collected_at = webhook.get_event_datetime()
                    
                elif webhook.order.status == "finished":
                    order.status = "delivered"
                    order.delivered_at = webhook.get_event_datetime()
                    
                    # Get delivery signature if available
                    for dest in webhook.order.destinations:
                        if dest.taskType == "delivery" and dest.taskResult.signedBy:
                            order.signed_by = dest.taskResult.signedBy
                            break
                
                order.save()
                
            except Order.DoesNotExist:
                # Log warning but return 200 to acknowledge receipt
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Order {webhook.order.externalId} not found for webhook")
        
        return JsonResponse({"status": "ok"}, status=200)
        
    except EasyTransError as e:
        # Log error and return 400
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Webhook error: {e}")
        return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# urls.py
# ==========================================

from django.urls import path
from . import views

urlpatterns = [
    path('api/easytrans/webhook/', views.easytrans_webhook, name='easytrans_webhook'),
]


# ==========================================
# management/commands/sync_customers.py
# ==========================================

from django.core.management.base import BaseCommand
from easytrans import Customer, CustomerContact
from services.easytrans_service import get_easytrans_client
from myapp.models import Company


class Command(BaseCommand):
    help = 'Sync customers to EasyTrans'

    def handle(self, *args, **options):
        client = get_easytrans_client()
        
        # Get all companies that need syncing
        companies = Company.objects.filter(sync_to_easytrans=True)
        
        customers = []
        for company in companies:
            # Build customer
            contacts = []
            for contact in company.contacts.all():
                contacts.append(CustomerContact(
                    contact_name=contact.name,
                    email=contact.email,
                    telephone=contact.phone,
                ))
            
            customer = Customer(
                company_name=company.name,
                address=company.address,
                houseno=company.house_number,
                postal_code=company.postal_code,
                city=company.city,
                country=company.country,
                external_id=str(company.id),
                customer_contacts=contacts,
            )
            customers.append(customer)
        
        # Import to EasyTrans
        if customers:
            result = client.import_customers(customers, mode="effect")
            
            # Update Django models with EasyTrans customer numbers
            for idx, customer_no in enumerate(result.new_customernos):
                companies[idx].easytrans_customer_no = customer_no
                companies[idx].save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully synced {len(customers)} customers')
            )
