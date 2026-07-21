# Reference Genomes
NIPPONBARE_GENBANK_PATH = ".data/Nipponbare_Ref/data/GCA_001433935.1/GCA_001433935.1_IRGSP-1.0_genomic.fna"
NIPPONBARE_REFSEQ_PATH = ".data/Nipponbare_Ref/data/GCF_001433935.1/GCF_001433935.1_IRGSP-1.0_genomic.fna"

# Sample DB Paths
HISTONE_DB_PATH = "data/histones_db.csv"
CHROMATIN_DB_PATH = "data/chromatin_db.csv"
DNA_METH_DB_PATH = "data/dna_meth_db.csv"

# Default HYPERPARAMS
BATCH_SIZE = 32
MAX_LENGTH = 512
MASKED_PCT = 0.15

EPOCHS = 5
EARLY_STOP_PATIENCE = 2

VALIDATION_PCT = 0.20

# COLUMNS
HISTONE_DB_COLS = [
    "Study",
    "Accession",
    "Cultivar",
    "Tissue",
    "Histone_Mod",
    "File_Name",
    "Link",
    "Path",
    "Notes",
]

CHROMATIN_DB_COLS = [
    "Study",
    "Accession",
    "Cultivar",
    "Tissue",
    "Method",
    "File_Name",
    "Link",
    "Path",
    "Notes",
]

DNA_METH_DB_COLS = [
    "Study",
    "Accession",
    "Cultivar",
    "Tissue",
    "File_Name",
    "Link",
    "Path",
    "Notes",
]

# Cultivars
NIPPONBARE = "Nipponbare"

# NIPPONBARE Seq ID to Chr Mapping
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

NIPPONBARE_ID_TO_CHR_NUM = {
    "AP014957.1": 1,
    "AP014958.1": 2,
    "AP014959.1": 3,
    "AP014960.1": 4,
    "AP014961.1": 5,
    "AP014962.1": 6,
    "AP014963.1": 7,
    "AP014964.1": 8,
    "AP014965.1": 9,
    "AP014966.1": 10,
    "AP014967.1": 11,
    "AP014968.1": 12,
}

CHR_NUM_TO_NIPPONBARE_ID = {
    1: "AP014957.1",
    2: "AP014958.1",
    3: "AP014959.1",
    4: "AP014960.1",
    5: "AP014961.1",
    6: "AP014962.1",
    7: "AP014963.1",
    8: "AP014964.1",
    9: "AP014965.1",
    10: "AP014966.1",
    11: "AP014967.1",
    12: "AP014968.1",
}

CHR_NUM_TO_CHR = {
    1: "Chr1",
    2: "Chr2",
    3: "Chr3",
    4: "Chr4",
    5: "Chr5",
    6: "Chr6",
    7: "Chr7",
    8: "Chr8",
    9: "Chr9",
    10: "Chr10",
    11: "Chr11",
    12: "Chr12",
}

# HISTONE_MARKS = [
#     "H3K23ac",
#     "H4K16ac",
#     "H3K4me3",
#     "H3K36me3",
#     "H3K27ac",
#     "H3K9ac",
#     "H4K12ac",
#     "H3K27me3",
#     "H3K4me1",
#     "H3K9me2"
# ]

# CHROMATIN_FEATURES = [
#     "ATAC-Seq",
#     "H3K4ac",
#     "H3K4me1",
#     "H3K4me2",
#     "H3K4me3",
#     "H3K9ac",
#     "H3K9me1",
#     "H3K9me2",
#     "H3K23ac",
#     "H3K27me3",
#     "H3K36me3",
#     "H4K12ac",
#     "H4K16ac"
# ]

KMERS = [3, 4, 5, 6]
BASES = ["A", "C", "G", "T"]

MODEL_KEYS = [
    "k3",
    "k4",
    "k5",
    "k6",
    "bpe"
]