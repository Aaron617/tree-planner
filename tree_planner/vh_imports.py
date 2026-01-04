"""
VirtualHome lazy import helper.

This module provides lazy imports for VirtualHome to handle cases where
VirtualHome is not installed or has installation issues on certain platforms.
"""

import sys
from typing import Optional, Any, Callable


class LazyImport:
    """Lazy import that only imports when accessed."""

    def __init__(self, module_path: str, pip_name: Optional[str] = None):
        self.module_path = module_path
        self.pip_name = pip_name or module_path.split('.')[0]
        self._module: Optional[Any] = None
        self._imported = False

    def _import(self):
        if self._imported:
            return self._module

        try:
            # Try importing from virtualhome package
            if self.module_path.startswith('virtualhome.'):
                # Import from virtualhome package
                import importlib
                self._module = importlib.import_module(self.module_path)
            else:
                # Try direct import
                import importlib
                self._module = importlib.import_module(self.module_path)
            self._imported = True
            return self._module
        except ImportError as e:
            # Provide helpful error message
            self._imported = True
            self._module = None
            return None

    def __getattr__(self, name):
        module = self._import()
        if module is None:
            raise ImportError(
                f"VirtualHome module '{self.module_path}' is not available. "
                f"Please install it with: uv pip install '{self.pip_name}' "
                f"or: pip install '{self.pip_name}'"
            )
        return getattr(module, name)

    def __call__(self, *args, **kwargs):
        module = self._import()
        if module is None:
            raise ImportError(
                f"VirtualHome module '{self.module_path}' is not available. "
                f"Please install it with: uv pip install '{self.pip_name}' "
                f"or: pip install '{self.pip_name}'"
            )
        return module(*args, **kwargs)


# Lazy VirtualHome imports
# These will only be imported when actually used
parse_script_line = LazyImport(
    'virtualhome.simulation.evolving_graph.scripts',
    'virtualhome'
).parse_script_line

# Environment and execution modules
EnvironmentGraph = LazyImport(
    'virtualhome.simulation.evolving_graph.environment',
    'virtualhome'
).EnvironmentGraph

EnvironmentState = LazyImport(
    'virtualhome.simulation.evolving_graph.environment',
    'virtualhome'
).EnvironmentState

ScriptExecutor = LazyImport(
    'virtualhome.simulation.evolving_graph.execution',
    'virtualhome'
).ScriptExecutor

# Utilities
read_script = LazyImport(
    'virtualhome.simulation.evolving_graph.scripts',
    'virtualhome'
).read_script

script_to_list_string = LazyImport(
    'virtualhome.simulation.evolving_graph.scripts',
    'virtualhome'
).script_to_list_string

read_script_from_list_string = LazyImport(
    'virtualhome.simulation.evolving_graph.scripts',
    'virtualhome'
).read_script_from_list_string

read_script_from_string = LazyImport(
    'virtualhome.simulation.evolving_graph.scripts',
    'virtualhome'
).read_script_from_string

Relation = LazyImport(
    'virtualhome.simulation.evolving_graph.execution',
    'virtualhome'
).Relation

State = LazyImport(
    'virtualhome.simulation.evolving_graph.execution',
    'virtualhome'
).State

graph_dict_helper = LazyImport(
    'virtualhome.simulation.evolving_graph.utils',
    'virtualhome'
).graph_dict_helper

load_name_equivalence = LazyImport(
    'virtualhome.simulation.evolving_graph.utils',
    'virtualhome'
).load_name_equivalence

# Preparation utilities
try:
    AddMissingScriptObjects = LazyImport(
        'virtualhome.simulation.evolving_graph.preparation',
        'virtualhome'
    ).AddMissingScriptObjects
except:
    AddMissingScriptObjects = None


def check_virtualhome_available() -> bool:
    """Check if VirtualHome is available."""
    try:
        import importlib
        importlib.import_module('virtualhome.simulation.evolving_graph.scripts')
        return True
    except ImportError:
        return False


def get_virtualhome_import_error() -> str:
    """Get helpful error message for VirtualHome installation."""
    return (
        "VirtualHome is not installed. Please install it using one of:\n"
        "  uv pip install virtualhome\n"
        "  pip install virtualhome\n"
        "Or install from GitHub:\n"
        "  pip install git+https://github.com/xavierpuigf/virtualhome.git\n\n"
        "If you encounter build issues on ARM64 macOS, try:\n"
        "  uv pip install --no-build-isolation opencv-python-headless"
    )
