# Tree-Planner

<div align="center">

**Close-loop Task Planning for Household Activities**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository contains the code for the paper: [Tree-Planner: Close-loop Task Planning for Household Activities](https://arxiv.org/abs/2310.08582)

</div>

---

## Overview

Tree-Planner implements AI-powered task decomposition and planning for household activities. It combines:

- **LLM-based Plan Generation**: Uses OpenAI's GPT models to decompose high-level household tasks into executable sub-tasks
- **Grounded Decision Making**: Validates plans against real-world constraints with error correction
- **VirtualHome Integration**: Simulates household environments for plan validation
- **Multi-process Support**: Parallel processing for faster plan generation

## Features

| Feature | Description |
|---------|-------------|
| 🤖 **Plan Generation** | Decomposes high-level tasks into executable sub-tasks using LLMs |
| ✅ **Grounded Deciding** | Validates plans against environment constraints with error correction |
| 🏠 **VirtualHome** | Full integration with VirtualHome simulator for execution |
| ⚡ **Multi-process** | Parallel processing for faster generation |
| 🌐 **Cross-Platform** | Works on Linux, macOS, and Windows |

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd tree-planner

# Install dependencies
uv sync

# Setup VirtualHome
uv pip install virtualhome
uv run python setup_virtualhome.py

# Test installation
uv run python test_e2e.py

# Run (requires OpenAI API key and data)
uv run python -m tree_planner.run
```

## Installation

### Prerequisites

- **Python 3.10 or higher** (required by VirtualHome)
- **[uv](https://github.com/astral-sh/uv)** package manager (recommended) or pip
- **OpenAI API key** for plan generation

### Standard Installation

#### Using uv (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd tree-planner

# Install dependencies
uv sync

# Setup VirtualHome
uv pip install virtualhome
uv run python setup_virtualhome.py
```

#### Using pip

```bash
# Clone repository
git clone <repository-url>
cd tree-planner

# Install in editable mode
pip install -e .

# Setup VirtualHome
pip install virtualhome
python setup_virtualhome.py
```

### VirtualHome Setup

The `setup_virtualhome.py` script handles:

1. **Fixing VirtualHome imports**: Makes Unity simulator optional (only Python-based simulation needed)
2. **Creating resource files**: Generates required JSON files:
   - `class_name_equivalence.json`
   - `properties_data.json`
   - `object_states.json`

#### Platform-Specific Notes

| Platform | Notes |
|----------|-------|
| **Linux** | Standard installation works |
| **macOS (Intel)** | Standard installation works |
| **macOS (ARM64)** | If opencv-python fails: <br> `uv pip install opencv-python-headless && uv pip install --no-deps virtualhome && uv run python setup_virtualhome.py` |
| **Windows** | Standard installation works (WSL2 recommended) |

## Configuration

### 1. OpenAI API Key

Create a `key.txt` file in the project root:

```
sk-...
sk-...
```

One key per line for multi-key rotation (useful for parallel processing).

### 2. Data Preparation

Prepare your data in the following structure:

```
dataplace/
├── data/
│   ├── TrimmedTestScene1_graph/
│   │   ├── task_to_graph.json     # Task to environment mapping
│   │   ├── train.json              # Training examples for few-shot
│   │   └── val.json                # Validation tasks
│   └── TrimmedTestScene2_graph/
│       └── ...
└── generation_results/
    └── TrimmedTestScene*_graph/    # Results will be saved here
```

**Task format (`val.json`)**:
```json
[
  {
    "task": "Clean the kitchen",
    "programs": {
      "task_description": "You need to clean the kitchen...",
      "goal_condition": [...]
    }
  }
]
```

**Graph format (`task_to_graph.json`)**:
```json
{
  "Clean the kitchen": {
    "nodes": [
      {"id": 1, "class_name": "kitchen", "category": "Rooms", ...},
      ...
    ],
    "edges": [...]
  }
}
```

## Usage

### Command Line

```bash
# Run full pipeline
uv run python -m tree_planner.run

# Or if installed system-wide
tree-planner
```

### Python API

```python
from tree_planner import run

# Run the full pipeline
run.main()
```

### Individual Components

```python
# Plan Generation only
from tree_planner.plan_generation import annotate_multi_process_run
from tree_planner.arguments import get_args

args = get_args()
results = annotate_multi_process_run(args)

# Grounded Deciding
from tree_planner.grounded_deciding import main
main(args)
```

## Project Structure

```
tree-planner/
├── tree_planner/                    # Main package
│   ├── __init__.py                  # Package initialization
│   ├── run.py                       # Entry point
│   ├── arguments.py                 # CLI argument parser
│   ├── plan_generation.py           # Plan generation module
│   ├── grounded_deciding.py         # Grounded decision module
│   ├── generation/                  # LLM generation
│   │   └── generator.py             # OpenAI API wrapper
│   ├── utils/                       # Utilities
│   │   ├── data_utils.py            # Data processing
│   │   ├── env_utils.py             # Environment prompt generation
│   │   ├── exec_utils.py            # Script execution
│   │   ├── retriever.py             # Semantic similarity
│   │   └── deciding_graph.py        # Decision tree for planning
│   ├── evolving_graph_patches/      # VirtualHome extensions
│   │   ├── custom_executor.py       # Custom script executor
│   │   └── custom_graph_dict_helper.py
│   └── prompt/                      # Prompt templates
│       ├── plan_generation_prompt.txt
│       ├── plan_generation_prompt_grounding.txt
│       ├── grounded_deciding_prompt.txt
│       └── grounded_deciding_prompt_error_correction.txt
├── pyproject.toml                   # Project configuration
├── uv.lock                          # Dependency lock file
├── setup_virtualhome.py             # VirtualHome setup script
├── test_e2e.py                      # End-to-end test
└── README.md
```

## Algorithm Pipeline

```
Input Task (e.g., "Clean the kitchen")
         │
         ▼
┌────────────────────────┐
│   Plan Generation      │
│   (OpenAI GPT)         │
└────────────────────────┘
         │
         ▼
   Multiple Plans
   (sample_n = 50)
         │
         ▼
┌────────────────────────┐
│   Post-processing      │
│   (Object translation)  │
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│   Grounded Deciding    │
│   (VirtualHome sim)     │
│   - Validate actions    │
│   - Error correction    │
│   - Majority voting    │
└────────────────────────┘
         │
         ▼
    Executable Plan
```

## Testing

### End-to-End Test

```bash
# Test all core components
uv run python test_e2e.py
```

This tests:
- Module imports
- VirtualHome integration
- Action format validation
- Graph difference calculation (GCR)
- Environment prompt generation
- Decision tree
- Custom graph helper

### Unit Tests

```bash
# Run pytest (if tests are added)
uv run pytest tests/
```

## Command-Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--temperature` | 0.8 (gen) / 0.7 (dec) | Sampling temperature |
| `--top_p` | 0.95 (gen) / 1.0 (dec) | Top-p sampling |
| `--sampling_n` | 50 (gen) / 20 (dec) | Number of samples |
| `--n_processes` | 5 | Parallel processes |
| `--n_shots` | 4 | Few-shot examples |
| `--retry_times` | 10 | Error correction retries |
| `--engine` | text-davinci-003 | OpenAI engine |

## Troubleshooting

### VirtualHome Import Errors

**Problem**: `ModuleNotFoundError: No module named 'unity_simulator'`

**Solution**: Run `uv run python setup_virtualhome.py`

### OpenAI API Errors

**Problem**: Authentication errors

**Solution**:
1. Check `key.txt` contains valid API key
2. Verify API key has sufficient credits

### Graph Execution Errors

**Problem**: Scripts fail to execute

**Solution**:
1. Check `task_to_graph.json` matches your task names
2. Verify graph has all required nodes and edges
3. Run `uv run python test_e2e.py` to verify setup

### ARM64 macOS Build Errors

**Problem**: opencv-python build fails

**Solution**:
```bash
uv pip install opencv-python-headless
uv pip install --no-deps virtualhome
uv run python setup_virtualhome.py
```

## Performance Tips

1. **Multi-key rotation**: Add multiple API keys to `key.txt` for faster parallel processing
2. **Adjust sampling_n**: Reduce `sampling_n` for faster iteration, increase for better quality
3. **Use GPU**: Install CUDA versions of PyTorch for faster transformer inference

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
- [OpenAI](https://openai.com/) - GPT models for plan generation
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

## Contact

For questions or issues, please open a GitHub issue or contact the maintainers.
