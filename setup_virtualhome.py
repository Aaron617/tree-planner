#!/usr/bin/env python
"""
Setup script for VirtualHome resources

This script downloads/creates necessary VirtualHome resource files
that may be missing from the pip installation.
"""

import os
import json
import sys
import subprocess


def create_virtualhome_resources():
    """Create VirtualHome resource files if missing."""

    # Find virtualhome installation path
    try:
        import virtualhome
        vh_path = os.path.dirname(virtualhome.__file__)
        resources_path = os.path.join(vh_path, 'resources')
    except ImportError:
        print("VirtualHome not installed. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'virtualhome'], check=True)
        import virtualhome
        vh_path = os.path.dirname(virtualhome.__file__)
        resources_path = os.path.join(vh_path, 'resources')

    os.makedirs(resources_path, exist_ok=True)
    print(f"VirtualHome resources path: {resources_path}")

    # Create class_name_equivalence.json
    class_name_equiv = os.path.join(resources_path, 'class_name_equivalence.json')
    if not os.path.exists(class_name_equiv):
        data = {
            "sofa": "sofa", "couch": "sofa",
            "fridge": "fridge", "refrigerator": "fridge",
            "tv": "television", "television": "television",
            "stove": "stove", "oven": "stove",
            "microwave": "microwave",
            "bed": "bed",
            "toilet": "toilet",
            "sink": "sink",
            "counter": "counter", "table": "table",
            "desk": "desk", "chair": "chair",
            "shelf": "shelf", "cupboard": "cupboard",
            "cabinet": "cabinet", "bathtub": "bathtub",
            "shower": "shower"
        }
        with open(class_name_equiv, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Created {class_name_equiv}")
    else:
        print(f"✓ {class_name_equiv} already exists")

    # Create properties_data.json
    properties_file = os.path.join(resources_path, 'properties_data.json')
    if not os.path.exists(properties_file):
        data = {
            "GRABBABLE": [
                "apple", "banana", "cup", "glass", "plate", "fork",
                "spoon", "knife", "remote", "phone", "book", "magazine",
                "towel", "soap", "newspaper", "pillow", "blanket"
            ],
            "CONTAINERS": [
                "fridge", "microwave", "oven", "cupboard", "cabinet",
                "sink", "toilet", "trash_can", "drawer", "shelf",
                "pot", "pan", "bathtub", "shower"
            ],
            "OBJECT_ORIENTED": [
                "tv", "computer", "laptop", "phone", "book", "magazine"
            ]
        }
        with open(properties_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Created {properties_file}")
    else:
        print(f"✓ {properties_file} already exists")

    # Create object_states.json
    states_file = os.path.join(resources_path, 'object_states.json')
    if not os.path.exists(states_file):
        data = {
            "OPEN": ["fridge", "microwave", "oven", "cupboard", "cabinet",
                     "drawer", "toilet", "bathtub"],
            "CLOSED": ["fridge", "microwave", "oven", "cupboard", "cabinet",
                        "drawer", "toilet"],
            "ON": ["stove", "tv", "computer", "lamp"],
            "OFF": ["stove", "tv", "computer", "lamp"],
            "CLEAN": ["plate", "cup", "glass", "fork", "spoon", "knife"],
            "DIRTY": ["plate", "cup", "glass", "fork", "spoon", "knife"],
            "PLUGGED_IN": ["tv", "computer", "lamp"],
            "UNPLUGGED": ["tv", "computer", "lamp"]
        }
        with open(states_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Created {states_file}")
    else:
        print(f"✓ {states_file} already exists")

    print()
    print("VirtualHome resources setup complete!")
    return resources_path


def fix_virtualhome_init():
    """Fix virtualhome/__init__.py to make unity_simulator optional."""

    try:
        import virtualhome
        vh_init = os.path.join(os.path.dirname(virtualhome.__file__), '__init__.py')

        with open(vh_init, 'r') as f:
            content = f.read()

        # Check if already fixed
        if 'try:' in content and 'unity_simulator' in content:
            print("✓ virtualhome/__init__.py already fixed")
            return

        # Write fixed version
        with open(vh_init, 'w') as f:
            f.write("""import glob
import sys
from sys import platform

# Optional: Unity simulator (not required for evolving_graph simulation)
try:
    original_path = sys.path[5]
    new_path = original_path + '/virtualhome/simulation'
    sys.path.append(new_path)
    from unity_simulator.comm_unity import UnityCommunication
    from unity_simulator import utils_viz
except (ImportError, IndexError, ValueError):
    # Unity simulator not available - this is OK for evolving_graph simulation
    UnityCommunication = None
    utils_viz = None
    pass
""")

        print("✓ Fixed virtualhome/__init__.py (made unity_simulator optional)")

    except Exception as e:
        print(f"Note: Could not fix virtualhome/__init__.py: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("VirtualHome Setup Script")
    print("=" * 60)
    print()

    print("Step 1: Installing/fixing VirtualHome...")
    fix_virtualhome_init()
    print()

    print("Step 2: Creating resource files...")
    create_virtualhome_resources()
    print()

    print("=" * 60)
    print("Setup complete! You can now run Tree-Planner.")
    print("=" * 60)
