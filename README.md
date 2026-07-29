# RiSPICE

RiSPICE (Rice SNP Prioritization Integrating Chromatin Effects) is a method for prioritizing non-coding rice variants by predicting their impact on chromatin features using a fine-tuned DNA language model.

This repository accompanies the paper:

> **Prioritizing Non-coding Variants in Rice GWAS Loci with a Chromatin-Informed DNA Language Model**

## What You Can Do with RiSPICE

RiSPICE provides an end-to-end workflow for analyzing the predicted chromatin effects of non-coding variants.

Using the provided RiSPICE models, you can:

- Predict chromatin feature probabilities for reference and alternate alleles.
- Compute **Per-Feature Scores** and **Overall Scores** to quantify the predicted impact of each variant.
- Prioritize variants by ranking them according to their Overall Scores.
- Analyze the predicted effects on individual chromatin features.
- Perform **in silico saturation mutagenesis** to identify impactful mutations within a genomic region.

The repository also includes the scripts used in this study for:

- Data preprocessing and dataset generation.
- Fine-tuning DNABERT-2 using LoRA.
- Model evaluation.

## Getting Started

To install RiSPICE and reproduce the complete OsHAK1 case study from the manuscript, see the **Getting Started** guide.

➡️ **Getting Started:** `getting-started/README.md`

Additional workflows and project documentation are available in the GitHub Wiki.

➡️ **GitHub Wiki:** https://github.com/bioinfodlsu/rispice/wiki

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
