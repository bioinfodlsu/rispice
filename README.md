# Rice Variant Prioritization

This repository contains the code, data processing scripts, and analysis pipeline developed for the paper: **Integrating Chromatin Features with a DNA Language Model Enables Prioritization of Non-coding Variants in Rice Association Studies**

## Overview

This work presents a method for predicting chromatin features from rice DNA sequences and prioritizing non-coding variants according to their predicted impact on chromatin state. The repository includes model training, evaluation, variant scoring, and downstream case study analyses.

## Models & Adapters

This project uses **[DNABERT-2-117M](https://huggingface.co/zhihan1996/DNABERT-2-117M)** as the base model, paired with fine-tuned LoRA adapters hosted on [Hugging Face](https://huggingface.co/):

* **Base Model:** [`zhihan1996/DNABERT-2-117M`](https://huggingface.co/zhihan1996/DNABERT-2-117M)
* **1000 bp Adapter:** [`paolomanlapaz/rice-variant-prioritization-1000bp`](https://huggingface.co/paolomanlapaz/rice-variant-prioritization-1000bp)
* **750 bp Adapter:** [`paolomanlapaz/rice-variant-prioritization-750bp`](https://huggingface.co/paolomanlapaz/rice-variant-prioritization-750bp)
* **500 bp Adapter:** [`paolomanlapaz/rice-variant-prioritization-500bp`](https://huggingface.co/paolomanlapaz/rice-variant-prioritization-500bp)

## Citation

If you use this repository, please cite the associated paper.

## License

This repository is intended for academic and research purposes.
