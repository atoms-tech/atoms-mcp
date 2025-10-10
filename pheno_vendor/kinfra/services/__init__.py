"""
KInfra Service Definitions

Pre-configured service definitions for common applications using KInfra infrastructure.
Makes it easy to spin up standardized services across projects.
"""

from .byteport import get_byteport_services, BytePortConfig

__all__ = ['get_byteport_services', 'BytePortConfig']
