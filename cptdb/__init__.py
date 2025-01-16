# FILE: /cptdb-package/cptdb-package/cptdb/__init__.py

"""
cptdb package

This package provides an interface to interact with a Redis database containing CPT (Current Procedural Terminology) codes and their hierarchies.

Available classes:
- CPTDB: A class to retrieve and manipulate CPT codes from Redis.

Usage:
Import the CPTDB class to access its methods for working with CPT codes.
"""

from .client import CPTDB

__all__ = ['CPTDB']
