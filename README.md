# RiSPICE

RiSPICE (Rice SNP Prioritization Integrating Chromatin Effects) is a method for prioritizing non-coding rice variants by predicting their impact on chromatin features using a fine-tuned DNA language model.

This repository accompanies the paper:

> **Integrating Chromatin Features with a DNA Language Model Enables Prioritization of Non-coding Variants in Rice Association Studies**

It includes:

- Data preprocessing and dataset generation
- Fine-tuning DNABERT-2 with LoRA
- Model evaluation
- Variant effect scoring
- Downstream case study analyses

## Overview

RiSPICE predicts chromatin feature changes caused by non-coding variants and ranks variants according to their predicted regulatory impact. The repository includes:

- Data preprocessing and dataset generation
- Fine-tuning DNABERT-2 with LoRA
- Model evaluation
- Variant effect scoring
- Downstream case study analyses

## Models & Adapters

RiSPICE uses **[DNABERT-2-117M](https://huggingface.co/zhihan1996/DNABERT-2-117M)** as the base model, paired with fine-tuned LoRA adapters hosted on [Hugging Face](https://huggingface.co/):

* **Base Model:** [`zhihan1996/DNABERT-2-117M`](https://huggingface.co/zhihan1996/DNABERT-2-117M)
* **1000 bp Adapter:** [`paolomanlapaz/rispice-1000bp`](https://huggingface.co/paolomanlapaz/rispice-1000bp)
* **750 bp Adapter:** [`paolomanlapaz/rispice-750bp`](https://huggingface.co/paolomanlapaz/rispice-750bp)
* **500 bp Adapter:** [`paolomanlapaz/rispice-500bp`](https://huggingface.co/paolomanlapaz/rispice-500bp)


## Citation

If you use RiSPICE in your research, please cite the associated paper.

## License

This project is released under the MIT License. See the LICENSE file for details.
