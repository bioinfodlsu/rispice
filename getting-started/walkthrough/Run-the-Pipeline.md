# Run the Pipeline

This walkthrough demonstrates how to generate chromatin feature predictions and compute Per-Feature and Overall scores for variants in the **OsHAK1** promoter.

## 1. Convert the VCF to `snp_list.tsv`

Convert the example VCF into RiSPICE's input format.

```bash
python -m scripts.snp.vcf_to_snp_list \
    -i getting-started/data/hak1.vcf.gz \
    -o .data/hak1/ \
    --nip_to_chrom
```

This generates:

```
.data/hak1/snp_list.tsv
```

## 2. Generate Reference and Alternate Sequences

Generate paired reference and alternate sequences for each variant.

```bash
python -m scripts.predict.generate_sequences \
    -i .data/hak1/snp_list.tsv \
    -o .data/hak1/ \
    -f .data/nipponbare/GCA_001433935.1_IRGSP-1.0_genomic.fna \
    -l 1000
```

This generates:

```
.data/hak1/sequences.tsv
```

The output contains the 1000 bp reference and alternate sequences for each variant, with the variant centered within the sequence.

> **Note**  
> This tutorial assumes the Nipponbare GenBank reference genome (`GCA_001433935.1_IRGSP-1.0_genomic.fna`) is stored in `.data/nipponbare/`. Update the path to match your local setup.

## 3. Predict Chromatin Features

Predict the probability of each chromatin feature for the reference and alternate sequences.

```bash
python -m scripts.predict.probs \
    -m .models/rispice-base \
    -l .models/rispice-1000bp \
    -i .data/hak1/sequences.tsv \
    -o .data/hak1/ \
    --cuda
```

This generates:

```
.data/hak1/ref.tsv
.data/hak1/alt.tsv
```

These files contain the predicted probabilities for each chromatin feature for the reference and alternate sequences, respectively.

> **Note**  
> Omit the `--cuda` flag if you are running on a CPU.

## 4. Compute Scores

Compute the **Per-Feature** and **Overall** Scores from the predicted probabilities.

```bash
python -m scripts.predict.compute_scores \
    -i .data/hak1 \
    -m log_odds \
    -f scores
```

This generates:
```
.data/hak1/scores.tsv
```

The output contains:

- **Per-Feature Scores**, representing the predicted change for each chromatin feature.
- **Overall Score**, computed as the Euclidean norm of the Per-Feature Scores.

The `-m log_odds` option computes the Per-Feature Scores as the **Difference in Log Odds** between the reference and alternate predictions.

## Next

The prediction pipeline has generated the Per-Feature and Overall Scores for each variant. Continue to **Analyze the Results** to rank the variants and investigate the chromatin features contributing to their predicted effects.

⬅️ **Previous:** [Getting Started](../README.md)

➡️ **Next:** [Analyze the Results](Analyze-Results.md)