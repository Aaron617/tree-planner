"""
Custom VirtualHome extensions for Tree-Planner.

This module provides custom implementations of VirtualHome components
that extend the standard VirtualHome functionality.
"""

# Apply monkey patches when imported
def apply_patches():
    """Apply custom patches to VirtualHome."""
    try:
        from virtualhome.simulation.evolving_graph import execution
        # Add custom helper classes if needed
        from . import custom_graph_dict_helper
        execution.custom_graph_dict_helper = custom_graph_dict_helper.custom_graph_dict_helper
    except ImportError:
        pass

# Auto-apply patches on import
try:
    apply_patches()
except Exception:
    pass
