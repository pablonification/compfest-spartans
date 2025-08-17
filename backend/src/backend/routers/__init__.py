"""Routers package for SmartBin backend."""

from . import health, scan, auth, ws

__all__ = ["health", "scan", "auth", "ws"]
