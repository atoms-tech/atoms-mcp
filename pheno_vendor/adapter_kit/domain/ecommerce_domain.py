"""E-Commerce Domain Model Example.

This complete example demonstrates Domain-Driven Design patterns
for an order management system.

Domain Concepts:
- Order (Aggregate Root)
- OrderItem (Entity within Order aggregate)
- Customer (Aggregate Root)
- Product (Aggregate Root)
- Money, Email, Address (Value Objects)
- OrderPlaced, OrderShipped (Domain Events)
- OrderSpecifications (Business Rules)
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

# Import domain-kit components
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from entities import AggregateRoot, Entity, UUID4Identity, AuditableEntity
from value_objects import Money, Currency, Email, Address, Country
from events import DomainEvent, event_handler
from specifications import Specification
from repositories import Repository, AsyncRepository
from services import DomainService


# =============================================================================
# VALUE OBJECTS
# =============================================================================

@dataclass(frozen=True)
class ProductSku(value_objects.ValueObject):  # type: ignore
    """Stock Keeping Unit for products."""

    code: str

    def __post_init__(self):
        if not self.code or len(self.code) < 3:
            raise ValueError("SKU must be at least 3 characters")


# =============================================================================
# DOMAIN EVENTS
# =============================================================================

@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    """Event raised when an order is placed."""

    order_id: str
    customer_id: str
    total_amount: Decimal
    currency: str
    item_count: int


@dataclass(frozen=True)
class OrderShipped(DomainEvent):
    """Event raised when an order is shipped."""

    order_id: str
    tracking_number: str
    shipped_to: str


@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    """Event raised when an order is cancelled."""

    order_id: str
    reason: str
    refund_amount: Decimal


@dataclass(frozen=True)
class PaymentProcessed(DomainEvent):
    """Event raised when payment is processed."""

    order_id: str
    amount: Decimal
    payment_method: str


# =============================================================================
# ENTITIES
# =============================================================================

@dataclass
class OrderItem(Entity[UUID]):
    """Order item entity - part of Order aggregate."""

    product_id: UUID4Identity
    product_name: str
    quantity: int
    unit_price: Money

    def __post_init__(self):
        """Validate order item."""
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.unit_price.amount <= 0:
            raise ValueError("Unit price must be positive")

    def total_price(self) -> Money:
        """Calculate total price for this item."""
        return self.unit_price * self.quantity

    def change_quantity(self, new_quantity: int) -> None:
        """Change item quantity."""
        if new_quantity <= 0:
            raise ValueError("Quantity must be positive")
        self.quantity = new_quantity
        self._mark_updated()


@dataclass
class Order(AggregateRoot[UUID]):
    """Order aggregate root.

    The Order is an aggregate that encapsulates order items and
    enforces business invariants.
    """

    customer_id: UUID4Identity
    shipping_address: Address
    status: str = "pending"
    items: List[OrderItem] = field(default_factory=list)
    tracking_number: Optional[str] = None

    def __post_init__(self):
        """Validate order invariants."""
        self.validate_invariants()

    def validate_invariants(self) -> None:
        """Validate business rules."""
        if not self.items:
            raise ValueError("Order must have at least one item")

        # All items must use same currency
        currencies = {item.unit_price.currency for item in self.items}
        if len(currencies) > 1:
            raise ValueError("All items must use the same currency")

    def add_item(self, product_id: UUID4Identity, product_name: str, quantity: int, unit_price: Money) -> None:
        """Add item to order."""
        if self.status != "pending":
            raise ValueError("Cannot modify order after it's been placed")

        # Check if item already exists
        for item in self.items:
            if item.product_id == product_id:
                item.change_quantity(item.quantity + quantity)
                self._mark_updated()
                return

        # Add new item
        item = OrderItem(
            id=UUID4Identity.generate(),
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
        )
        self.items.append(item)
        self._mark_updated()

    def remove_item(self, item_id: UUID4Identity) -> None:
        """Remove item from order."""
        if self.status != "pending":
            raise ValueError("Cannot modify order after it's been placed")

        self.items = [item for item in self.items if item.id != item_id]
        if not self.items:
            raise ValueError("Order must have at least one item")
        self._mark_updated()

    def total_amount(self) -> Money:
        """Calculate total order amount."""
        if not self.items:
            return Money.zero(Currency.USD)

        total = self.items[0].total_price()
        for item in self.items[1:]:
            total = total + item.total_price()
        return total

    def place_order(self) -> None:
        """Place the order - transition to placed status."""
        if self.status != "pending":
            raise ValueError(f"Cannot place order in {self.status} status")

        self.validate_invariants()
        self.status = "placed"
        self._mark_updated()

        # Raise domain event
        event = OrderPlaced(
            order_id=str(self.id),
            customer_id=str(self.customer_id),
            total_amount=self.total_amount().amount,
            currency=self.total_amount().currency.value,
            item_count=len(self.items),
        )
        self.raise_event(event)

    def ship_order(self, tracking_number: str) -> None:
        """Ship the order."""
        if self.status != "placed":
            raise ValueError(f"Cannot ship order in {self.status} status")

        self.status = "shipped"
        self.tracking_number = tracking_number
        self._mark_updated()

        # Raise domain event
        event = OrderShipped(
            order_id=str(self.id),
            tracking_number=tracking_number,
            shipped_to=self.shipping_address.format(),
        )
        self.raise_event(event)

    def cancel_order(self, reason: str) -> None:
        """Cancel the order."""
        if self.status in ("shipped", "delivered"):
            raise ValueError(f"Cannot cancel order in {self.status} status")

        old_status = self.status
        self.status = "cancelled"
        self._mark_updated()

        # Raise domain event if order was placed
        if old_status == "placed":
            event = OrderCancelled(
                order_id=str(self.id),
                reason=reason,
                refund_amount=self.total_amount().amount,
            )
            self.raise_event(event)


@dataclass
class Customer(AggregateRoot[UUID]):
    """Customer aggregate root."""

    email: Email
    name: str
    billing_address: Address
    shipping_address: Optional[Address] = None
    tier: str = "standard"  # standard, gold, platinum

    def upgrade_to_gold(self) -> None:
        """Upgrade customer to gold tier."""
        if self.tier == "standard":
            self.tier = "gold"
            self._mark_updated()

    def is_premium(self) -> bool:
        """Check if customer is premium (gold or platinum)."""
        return self.tier in ("gold", "platinum")


# =============================================================================
# SPECIFICATIONS
# =============================================================================

class OrderIsPlaced(Specification[Order]):
    """Specification for placed orders."""

    def is_satisfied_by(self, order: Order) -> bool:
        return order.status == "placed"


class OrderIsShippable(Specification[Order]):
    """Specification for orders ready to ship."""

    def is_satisfied_by(self, order: Order) -> bool:
        return order.status == "placed" and order.total_amount().is_positive()


class OrderExceedsAmount(Specification[Order]):
    """Specification for orders exceeding a certain amount."""

    def __init__(self, minimum_amount: Money):
        self.minimum_amount = minimum_amount

    def is_satisfied_by(self, order: Order) -> bool:
        return order.total_amount() >= self.minimum_amount


class CustomerIsPremium(Specification[Customer]):
    """Specification for premium customers."""

    def is_satisfied_by(self, customer: Customer) -> bool:
        return customer.is_premium()


# =============================================================================
# DOMAIN SERVICES
# =============================================================================

class OrderPricingService(DomainService):
    """Domain service for order pricing calculations."""

    def calculate_shipping_cost(self, order: Order, customer: Customer) -> Money:
        """Calculate shipping cost based on order and customer."""
        base_cost = Money(Decimal("9.99"), Currency.USD)

        # Free shipping for premium customers
        if customer.is_premium():
            return Money.zero(Currency.USD)

        # Free shipping for orders over $50
        if order.total_amount() >= Money(Decimal("50.00"), Currency.USD):
            return Money.zero(Currency.USD)

        return base_cost

    def calculate_tax(self, order: Order) -> Money:
        """Calculate tax for order."""
        tax_rate = Decimal("0.08")  # 8% tax

        # Tax-exempt for certain states
        if order.shipping_address.state in ("OR", "NH"):
            return Money.zero(order.total_amount().currency)

        return order.total_amount() * tax_rate


class OrderFulfillmentService(DomainService):
    """Domain service for order fulfillment."""

    def can_fulfill_order(self, order: Order) -> bool:
        """Check if order can be fulfilled."""
        # Check business rules
        if not OrderIsShippable().is_satisfied_by(order):
            return False

        # Additional fulfillment checks would go here
        # (inventory, shipping restrictions, etc.)
        return True

    def prepare_shipment(self, order: Order) -> str:
        """Prepare order for shipment and return tracking number."""
        if not self.can_fulfill_order(order):
            raise ValueError("Order cannot be fulfilled")

        # Generate tracking number (simplified)
        import random
        tracking = f"TRACK-{random.randint(100000, 999999)}"

        return tracking


# =============================================================================
# REPOSITORIES
# =============================================================================

class OrderRepository(Repository[Order, UUID]):
    """Repository for Order aggregates."""

    def __init__(self):
        self._orders: dict[UUID4Identity, Order] = {}

    def get(self, entity_id: UUID4Identity) -> Optional[Order]:  # type: ignore
        """Get order by ID."""
        return self._orders.get(entity_id)

    def add(self, entity: Order) -> None:
        """Add new order."""
        self._orders[entity.id] = entity

    def update(self, entity: Order) -> None:
        """Update existing order."""
        self._orders[entity.id] = entity

    def remove(self, entity: Order) -> None:
        """Remove order."""
        if entity.id in self._orders:
            del self._orders[entity.id]

    def find(self, specification: Specification[Order]) -> List[Order]:  # type: ignore
        """Find orders matching specification."""
        return [
            order
            for order in self._orders.values()
            if specification.is_satisfied_by(order)
        ]

    def find_by_customer(self, customer_id: UUID4Identity) -> List[Order]:
        """Find all orders for a customer."""
        return [
            order
            for order in self._orders.values()
            if order.customer_id == customer_id
        ]


# =============================================================================
# EVENT HANDLERS
# =============================================================================

@event_handler(OrderPlaced)
def send_order_confirmation(event: OrderPlaced):
    """Send order confirmation email when order is placed."""
    print(f"📧 Sending order confirmation for order {event.order_id}")
    print(f"   Total: {event.total_amount} {event.currency}")
    print(f"   Items: {event.item_count}")


@event_handler(OrderShipped)
def send_shipping_notification(event: OrderShipped):
    """Send shipping notification when order ships."""
    print(f"📦 Order {event.order_id} has been shipped!")
    print(f"   Tracking: {event.tracking_number}")
    print(f"   Destination: {event.shipped_to}")


@event_handler(OrderCancelled)
def process_refund(event: OrderCancelled):
    """Process refund when order is cancelled."""
    print(f"💰 Processing refund for order {event.order_id}")
    print(f"   Amount: {event.refund_amount}")
    print(f"   Reason: {event.reason}")


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

def example_usage():
    """Demonstrate the e-commerce domain model."""
    from events import get_event_publisher

    print("=" * 80)
    print("E-COMMERCE DOMAIN MODEL EXAMPLE")
    print("=" * 80)

    # Create customer
    customer = Customer(
        id=UUID4Identity.generate(),
        email=Email("john.doe@example.com"),
        name="John Doe",
        billing_address=Address(
            street="123 Main St",
            city="Portland",
            state="OR",
            postal_code="97201",
            country=Country.US,
        ),
        tier="gold",
    )
    print(f"\n✅ Created customer: {customer.name} ({customer.email})")
    print(f"   Tier: {customer.tier}")

    # Create order
    order = Order(
        id=UUID4Identity.generate(),
        customer_id=customer.id,
        shipping_address=customer.billing_address,
    )
    print(f"\n✅ Created order: {order.id}")

    # Add items to order
    order.add_item(
        product_id=UUID4Identity.generate(),
        product_name="Laptop",
        quantity=1,
        unit_price=Money(Decimal("999.99"), Currency.USD),
    )
    order.add_item(
        product_id=UUID4Identity.generate(),
        product_name="Mouse",
        quantity=2,
        unit_price=Money(Decimal("29.99"), Currency.USD),
    )
    print(f"\n✅ Added {len(order.items)} items to order")
    for item in order.items:
        print(f"   - {item.product_name}: {item.quantity} x {item.unit_price}")

    # Calculate pricing
    pricing_service = OrderPricingService()
    shipping = pricing_service.calculate_shipping_cost(order, customer)
    tax = pricing_service.calculate_tax(order)

    print(f"\n💰 Order totals:")
    print(f"   Subtotal: {order.total_amount()}")
    print(f"   Shipping: {shipping}")
    print(f"   Tax: {tax}")
    print(f"   Grand Total: {order.total_amount() + shipping + tax}")

    # Apply specifications
    print(f"\n🔍 Business rules:")
    print(f"   Can ship? {OrderIsShippable().is_satisfied_by(order)}")
    print(f"   Over $100? {OrderExceedsAmount(Money(Decimal('100'), Currency.USD)).is_satisfied_by(order)}")
    print(f"   Customer premium? {CustomerIsPremium().is_satisfied_by(customer)}")

    # Place order (will trigger event)
    print(f"\n📋 Placing order...")
    order.place_order()

    # Fulfill order
    fulfillment_service = OrderFulfillmentService()
    if fulfillment_service.can_fulfill_order(order):
        tracking = fulfillment_service.prepare_shipment(order)
        order.ship_order(tracking)

    # Save to repository
    repo = OrderRepository()
    repo.add(order)

    print(f"\n✅ Order complete! Status: {order.status}")
    print(f"   Repository contains {len(repo._orders)} orders")

    # Demonstrate event publishing
    publisher = get_event_publisher()
    events = order.get_domain_events()
    print(f"\n📢 Publishing {len(events)} domain events...")
    for event in events:
        publisher.publish(event)

    print("\n" + "=" * 80)


if __name__ == "__main__":
    example_usage()
