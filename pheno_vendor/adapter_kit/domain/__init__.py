"""Entity base classes for Domain-Driven Design.

Entities have identity that runs through time and different representations.
They are distinguished by their identity rather than their attributes.
"""

from .entity import Entity
from .aggregate_root import AggregateRoot
from .identity import Identity, UUID4Identity, StringIdentity, IntegerIdentity

__all__ = [
    "Entity",
    "AggregateRoot",
    "Identity",
    "UUID4Identity",
    "StringIdentity",
    "IntegerIdentity",
]
