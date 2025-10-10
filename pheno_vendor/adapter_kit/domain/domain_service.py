"""Domain Service base class."""

from abc import ABC


class DomainService(ABC):
    """Base class for domain services.

    Domain services contain domain logic that doesn't naturally fit within
    an entity or value object. They are:
    - Stateless
    - Named after domain activities (verbs)
    - Operate on domain objects
    - Don't have identity

    Use domain services when:
    - The operation involves multiple aggregates
    - The logic doesn't belong to any single entity
    - The operation is a significant domain concept

    Example:
        >>> from domain_kit.services import DomainService
        >>>
        >>> class MoneyTransferService(DomainService):
        ...     '''Domain service for transferring money between accounts.'''
        ...
        ...     def transfer(
        ...         self,
        ...         from_account: Account,
        ...         to_account: Account,
        ...         amount: Money
        ...     ) -> None:
        ...         '''Transfer money from one account to another.'''
        ...         # Domain logic
        ...         if from_account.balance < amount:
        ...             raise InsufficientFundsError()
        ...
        ...         from_account.withdraw(amount)
        ...         to_account.deposit(amount)
        ...
        ...         # Raise domain events
        ...         event = MoneyTransferred(
        ...             from_account_id=str(from_account.id),
        ...             to_account_id=str(to_account.id),
        ...             amount=amount.amount,
        ...             currency=amount.currency.value
        ...         )
        ...         from_account.raise_event(event)
        >>>
        >>> # Usage
        >>> transfer_service = MoneyTransferService()
        >>> transfer_service.transfer(account1, account2, Money(100, Currency.USD))
    """

    pass


class CommandHandler(DomainService):
    """Base class for command handlers (CQRS pattern).

    Command handlers process commands and coordinate domain logic.
    They typically:
    - Validate the command
    - Load necessary aggregates
    - Execute domain logic
    - Persist changes
    - Publish events

    Example:
        >>> class PlaceOrderCommandHandler(CommandHandler):
        ...     def __init__(self, order_repository, product_repository):
        ...         self.orders = order_repository
        ...         self.products = product_repository
        ...
        ...     def handle(self, command: PlaceOrderCommand) -> OrderId:
        ...         # Validate
        ...         if not command.items:
        ...             raise ValueError("Order must have items")
        ...
        ...         # Load aggregates
        ...         products = [
        ...             self.products.get(item.product_id)
        ...             for item in command.items
        ...         ]
        ...
        ...         # Create aggregate
        ...         order = Order.create(
        ...             customer_id=command.customer_id,
        ...             items=command.items,
        ...             products=products
        ...         )
        ...
        ...         # Persist
        ...         self.orders.add(order)
        ...
        ...         return order.id
    """

    pass


class QueryHandler(DomainService):
    """Base class for query handlers (CQRS pattern).

    Query handlers retrieve data without modifying state.
    They typically:
    - Load read models
    - Apply business logic for data presentation
    - Return DTOs

    Example:
        >>> class GetOrderDetailsQueryHandler(QueryHandler):
        ...     def __init__(self, order_repository):
        ...         self.orders = order_repository
        ...
        ...     def handle(self, query: GetOrderDetailsQuery) -> OrderDetailsDTO:
        ...         order = self.orders.get(query.order_id)
        ...         if not order:
        ...             raise OrderNotFoundError(query.order_id)
        ...
        ...         return OrderDetailsDTO(
        ...             order_id=str(order.id),
        ...             customer_id=order.customer_id,
        ...             items=[self._to_dto(item) for item in order.items],
        ...             total=order.total_amount(),
        ...             status=order.status
        ...         )
    """

    pass
