from pathlib import Path

NIPPONBARE_ID_TO_CHR = {
    "AP014957.1": "Chr1",
    "AP014958.1": "Chr2",
    "AP014959.1": "Chr3",
    "AP014960.1": "Chr4",
    "AP014961.1": "Chr5",
    "AP014962.1": "Chr6",
    "AP014963.1": "Chr7",
    "AP014964.1": "Chr8",
    "AP014965.1": "Chr9",
    "AP014966.1": "Chr10",
    "AP014967.1": "Chr11",
    "AP014968.1": "Chr12",
}

def capitalize_chr(input_f: Path):
    tmp_f = input_f.with_suffix(".tmp")

    with open(input_f) as f_in, open(tmp_f, "w") as f_out:
        for line in f_in:
            if line.startswith("#"):
                f_out.write(line)
                continue

            parts = line.rstrip().split("\t")
            chrom = parts[0]

            # Case 1: Convert accession IDs
            if chrom in NIPPONBARE_ID_TO_CHR:
                parts[0] = NIPPONBARE_ID_TO_CHR[chrom]

            # Case 2: Normalize chr / Chr / CHR...
            elif chrom.lower().startswith("chr"):
                parts[0] = "Chr" + chrom[3:]

            f_out.write("\t".join(parts) + "\n")

    tmp_f.replace(input_f)  # atomically replace original file

# Example usage:
PEAKS_DIR = Path(".data2/prep/profiles/peaks5")
peaks_subdirs = [x for x in PEAKS_DIR.iterdir() if x.is_dir()]
for feature in peaks_subdirs:
    print(f"[Processing {feature.stem}]")
    files = [p for p in feature.iterdir() if p.is_file()]
    
    for f in files:
        print(f"*{f.name}")
        capitalize_chr(f)