"""
dYdX v4 Perpetual Trading Bot

Protocol-First Implementation using official dydx-v4-client
"""

__version__ = "0.1.0"
__author__ = "dYdX Trader"
__license__ = "MIT"

# Core exports - protocol-first approach
from .config.settings import Settings
from .connection.dydx_client import DydxClientManager

__all__ = [
    "Settings",
    "DydxClientManager",
]
