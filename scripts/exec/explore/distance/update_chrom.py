from pathlib import Path

MAIN_DIR = Path("data/macs3/histone")
FIXED_DIR = MAIN_DIR / "fixed_chrom_consensus"
HISTONE_MARKS = [
    "H3K23ac",
    "H4K16ac",
    "H3K4me3",
    "H3K36me3",
    "H3K27ac",
    "H3K9ac",
    "H4K12ac",
    "H3K27me3",
    "H3K4me1",
    "H3K9me2"
]

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


VALID_CHROMS = {f"chr{i}" for i in range(1,13)}

FIXED_DIR.mkdir(parents=True, exist_ok=True)

for histone in HISTONE_MARKS:
    fname = f"{histone}_consensus_merged.bed"
    input_f = MAIN_DIR / histone / fname
    output_f = FIXED_DIR / fname
    
    if not input_f.exists():
        print(f"Skipping: {input_f} not found.")
        continue
    
    print(f"Processing {input_f}")
    unknown_chroms = set()
    with open(input_f, "r") as fin, open(output_f, "w") as fout:
        for line in fin:
            if not line.strip(): continue  # Skip empty lines
            
            columns = line.strip().split("\t")
            chrom = columns[0]
            
            # Step 1: apply Nipponbare mapping
            chrom = NIPPONBARE_ID_TO_CHR.get(chrom, chrom)

            # Step 2: add chr prefix if numeric
            if chrom.isdigit():
                chrom = f"chr{chrom}"

            # Step 3: normalize Chr → chr
            chrom = chrom.lower()
            
            # Step 3: validate chromosome
            if chrom not in VALID_CHROMS:
                unknown_chroms.add(columns[0])
                continue  # skip incorrect mapping
            
            columns[0] = chrom
            fout.write("\t".join(columns) + "\n")
    
    if unknown_chroms:
        print(f"WARNING: Unknown chromosomes in {histone}: {sorted(unknown_chroms)}")

    print(f"Finished {output_f}")