"""TechHunt connector package.

Usage
-----
Import the base interface to create a new connector:

    from connectors.base import EventConnector, NormalizedEvent

The mock connector is always available:

    from connectors.mock import MockConnector

All other connectors are placeholder stubs that raise NotImplementedError
until credentials and permission status are confirmed.
"""
