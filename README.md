# RiSPICE

RiSPICE (Rice SNP Prioritization Integrating Chromatin Effects) is a method for prioritizing non-coding rice variants by predicting their impact on chromatin features using a fine-tuned DNA language model.

This repository accompanies the paper:

> **Prioritizing Non-coding Variants in Rice GWAS Loci with a Chromatin-Informed DNA Language Model**

It includes:

- Data preprocessing and dataset generation
- Fine-tuning DNABERT-2 with LoRA
- Model evaluation
- Variant effect scoring
- Downstream case study analyses

## Quick Start

See the **[Quick Start Guide](https://github.com/bioinfodlsu/rispice/wiki/Quick-Start)** for installation instructions and examples of running RiSPICE.

## Models & Adapters

RiSPICE builds upon **[DNABERT-2-117M](https://huggingface.co/zhihan1996/DNABERT-2-117M)**. We provide the RiSPICE Base model together with LoRA adapters for different input sequence lengths.

- **RiSPICE Base:** [`paolomanlapaz/rispice-base`](https://huggingface.co/paolomanlapaz/rispice-base)
- **1000 bp Adapter:** [`paolomanlapaz/rispice-1000bp`](https://huggingface.co/paolomanlapaz/rispice-1000bp)
- **750 bp Adapter:** [`paolomanlapaz/rispice-750bp`](https://huggingface.co/paolomanlapaz/rispice-750bp)
- **500 bp Adapter:** [`paolomanlapaz/rispice-500bp`](https://huggingface.co/paolomanlapaz/rispice-500bp)

Download the RiSPICE Base model together with the desired LoRA adapter before running inference.

```bash
hf download <repo_id> --local-dir <local_directory>
```

## Citation

If you use RiSPICE in your research, please cite the associated paper.

## License

This project is released under the MIT License. See the LICENSE file for details.
