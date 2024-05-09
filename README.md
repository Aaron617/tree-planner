This repository contains the code of https://arxiv.org/abs/2310.08582.

## Requirements

We have made necessary improvements to the existing VirtualHome 1.0.0 to adapt it to the close-loop task planning setting. Specifically, we have moved all the files from the `evolving_graph/` folder in the original repository to `virtualhome/evolving_graph/` in our modified version.

## Setup

1. Install the required packages by running:

```
pip install -r requirements.txt
```

2. Move the files from the `evolving_graph/` folder to `virtualhome/evolving_graph/`.

## Running the Code

To run the code, execute the following command:

```
python run.py
```

This will start the close-loop task planning process using the improved VirtualHome simulator.
