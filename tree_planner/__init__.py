"""
Tree-Planner: Close-loop task planning for household activities.

This package provides AI-powered task decomposition and planning for
household activities, integrated with VirtualHome simulator.
"""

__version__ = "0.1.0"

# Apply VirtualHome patches on import
from . import evolving_graph_patches  # noqa: F401
