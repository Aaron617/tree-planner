# Tree-Planner

This repository contains the code of https://arxiv.org/abs/2310.08582.

## 📌 Note: Refactored Version Available

This is the **original codebase** which requires manual VirtualHome setup.

We have created a **refactored version** in the [`refactor/virtualhome-standard`](https://github.com/your-repo/tree/refactor/virtualhome-standard) branch that:

- ✅ Works with standard `pip install virtualhome`
- ✅ Uses `uv` package manager for easier setup
- ✅ Includes automated setup scripts
- ✅ Has comprehensive documentation
- ✅ Supports cross-platform usage (Linux, macOS, Windows)

### To use the refactored version:

```bash
git checkout refactor/virtualhome-standard
```

See the [README in that branch](https://github.com/your-repo/tree/refactor/virtualhome-standard) for detailed installation instructions.

---

## Original Setup Instructions

### Requirements

We have made necessary improvements to the existing VirtualHome 1.0.0 to adapt it to the close-loop task planning setting. Specifically, we have moved all the files from the `evolving_graph/` folder in the original repository to `virtualhome/evolving_graph/` in our modified version.

### Setup

1. Install the required packages by running:

```
pip install -r requirements.txt
```

2. Move the files from the `evolving_graph/` folder to `virtualhome/evolving_graph/`.

### Running the Code

To run the code, execute the following command:

```
python run.py
```

This will start the close-loop task planning process using the improved VirtualHome simulator.

---

## Citation

If you use this code in your research, please cite:

```bibtex
@article{hu2023tree,
  title={Tree-planner: Efficient close-loop task planning with large language models},
  author={Hu, Mengkang and Mu, Yao and Yu, Xinmiao and Ding, Mingyu and Wu, Shiguang and Shao, Wenqi and Chen, Qiguang and Wang, Bin and Qiao, Yu and Luo, Ping},
  journal={arXiv preprint arXiv:2310.08582},
  year={2023}
}
```
