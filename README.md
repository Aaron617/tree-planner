# Tree-Planner

Close-loop task planning for household activities using VirtualHome simulator.

This repository contains the code for the paper: https://arxiv.org/abs/2310.08582.

## Overview

Tree-Planner implements AI-powered task decomposition and planning for household activities. It uses OpenAI's GPT models to generate task plans and validates them against the VirtualHome environment simulation.

## Features

- **Plan Generation**: Uses LLMs to decompose high-level household tasks into executable sub-tasks
- **Grounded Deciding**: Validates plans against real-world constraints with error correction
- **VirtualHome Integration**: Standard integration with VirtualHome simulator
- **Multi-process Support**: Parallel processing for faster plan generation
- **Cross-Platform**: Works on Linux, macOS, and Windows with uv package manager

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Standard Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd tree-planner
```

2. Install using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

### VirtualHome Setup (Optional)

VirtualHome is required for full execution simulation. Installation may vary by platform:

#### Linux
```bash
uv pip install virtualhome
```

#### macOS (Intel)
```bash
uv pip install virtualhome
```

#### macOS (ARM64/M1/M2/M3)
VirtualHome has dependency build issues on ARM64. Workaround:
```bash
uv pip install opencv-python-headless
uv pip install --no-deps virtualhome
uv pip install -r <(uv pip show virtualhome | grep "Requires:" | sed 's/Requires: //')
```

Or install from local source if you have the simulation directory:
```bash
# Place VirtualHome simulation/ directory in project root
# Then use local installation mode
```

#### Windows
```bash
uv pip install virtualhome
```

**Note**: If VirtualHome installation fails, core features (plan generation) still work. Only execution simulation requires VirtualHome.

## Usage

### Command Line

Run the full pipeline:
```bash
uv run python -m tree_planner.run
```

Or if installed:
```bash
tree-planner
```

### As a Python Module

```python
from tree_planner import run

# Run the full pipeline
run.main()
```

### Without VirtualHome

Core planning features work without VirtualHome:
```python
from tree_planner.plan_generation import main as gen_main
from tree_planner.generation.generator import Generator

# Generate plans (no execution simulation)
```

## Project Structure

```
tree-planner/
├── tree_planner/
│   ├── __init__.py              # Package initialization
│   ├── run.py                   # Main entry point
│   ├── arguments.py             # CLI argument parser
│   ├── plan_generation.py       # Plan generation module
│   ├── grounded_deciding.py     # Grounded decision module (needs VH)
│   ├── generation/
│   │   └── generator.py         # OpenAI API wrapper
│   ├── utils/
│   │   ├── data_utils.py        # Data processing
│   │   ├── env_utils.py         # Environment utilities (needs VH)
│   │   ├── exec_utils.py        # Execution utilities (needs VH)
│   │   ├── retriever.py         # Semantic retrieval
│   │   └── deciding_graph.py    # Decision tree implementation
│   ├── evolving_graph_patches/  # Custom VirtualHome extensions
│   │   ├── custom_executor.py
│   │   └── custom_graph_dict_helper.py
│   └── prompt/                  # Prompt templates
├── pyproject.toml               # Project configuration
├── uv.lock                      # Dependency lock file
└── README.md
```

## Configuration

1. Create a `key.txt` file with your OpenAI API key (one per line for multi-key support)

2. Prepare your data:
   - Task descriptions in JSON format
   - Environment graph files
   - Task-to-graph mappings

## Development

### Install in Development Mode

```bash
uv sync --all-extras
```

### Running Tests

```bash
uv run pytest tests/
```

### Code Formatting

```bash
uv run black tree_planner/
uv run flake8 tree_planner/
```

## Platform-Specific Notes

### macOS (ARM64)
- VirtualHome installation may fail due to opencv-python build issues
- Use `opencv-python-headless` as workaround
- Core planning features work without VirtualHome

### Linux
- All features supported
- Recommend using conda/mamba for better dependency management

### Windows
- All features supported
- Use WSL2 for better compatibility

## Citation

If you use this code in your research, please cite:

```bibtex
@article{tree-planner-2023,
  title={Tree-Planner: Close-loop Task Planning for Household Activities},
  author={...},
  journal={...},
  year={2023},
  url={https://arxiv.org/abs/2310.08582}
}
```

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [VirtualHome](http://virtual-home.org/) - Household activity simulation platform
- OpenAI - GPT models for plan generation
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
