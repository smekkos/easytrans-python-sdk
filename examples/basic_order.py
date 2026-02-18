"""
Basic order creation example.

This example shows how to create and submit a simple order to EasyTrans.
"""

from easytrans import EasyTransClient, Order, Destination, Package
from easytrans.constants import CollectDeliver

# Initialize client
client = EasyTransClient(
    server_url="mytrans.nl",  # Your server URL
    environment_name="demo",  # Your environment name
    username="your_username",
    password="your_password",
    default_mode="test",  # Start with test mode
)

# Create pickup destination
pickup = Destination(
    collect_deliver=CollectDeliver.PICKUP.value,
    company_name="Sender Company",
    contact="John Doe",
    address="Keizersgracht",
    houseno="1",
    postal_code="1015CC",
    city="Amsterdam",
    country="NL",
    telephone="020-1234567",
    destination_remark="Call before arrival",
)

# Create delivery destination
delivery = Destination(
    collect_deliver=CollectDeliver.DELIVERY.value,
    company_name="Receiver Company",
    contact="Jane Smith",
    address="Kanaalweg",
    houseno="14",
    postal_code="3526KL",
    city="Utrecht",
    country="NL",
    telephone="030-7654321",
    customer_reference="ORDER-123",
)

# Create package information
package = Package(
    amount=2.0,  # 2 packages
    weight=150.0,  # kg per package
    length=120.0,  # cm
    width=80.0,
    height=50.0,
    description="Euro pallets",
)

# Create order
order = Order(
    productno=2,  # Your product number from EasyTrans
    date="2026-02-18",  # Pickup date
    time="14:00",  # Pickup time
    status="submit",  # "submit", "save", or "quote"
    remark="2 Euro pallets with goods",
    remark_invoice="PO Number: ABC123",
    email_receiver="receiver@example.com",
    external_id="my-system-order-123",  # Your internal order ID
    order_destinations=[pickup, delivery],
    order_packages=[package],
)

# Test the order first (validation only)
print("Testing order...")
test_result = client.import_orders([order], mode="test")
print(f"✓ Validation passed: {test_result.total_orders} order(s)")

# If validation passes, submit for real
print("\nSubmitting order...")
result = client.import_orders([order], mode="effect")

print(f"✓ Order created successfully!")
print(f"  Order number: {result.new_ordernos[0]}")
print(f"  Tracking number: {result.order_tracktrace[str(result.new_ordernos[0])].local_trackingnr}")
print(f"  Track & Trace URL: {result.order_tracktrace[str(result.new_ordernos[0])].local_tracktrace_url}")

# You can also request rates
print("\nGetting rates...")
result_with_rates = client.import_orders([order], mode="test", return_rates=True)
if result_with_rates.order_rates:
    print("Rates calculated (test mode)")
