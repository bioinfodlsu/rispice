import subprocess, math
from pathlib import Path

FEATURE = "H4K16ac"
BASE_DIR = Path(f"data/macs3/histone/{FEATURE}")

def computeIntersections(feature=FEATURE, path=BASE_DIR):
    command = f"bedtools multiinter -i {path}/*.narrowPeak > {path}/{feature}_multiinter.bed"
    subprocess.run(command, shell=True, check=True)

def countFiles(path=BASE_DIR):
    command = f"ls {path}/*.narrowPeak | wc -l"
    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
    return int(result.stdout.strip())

def computeThreshold(count:int):
    return math.ceil(count/2)

def filterPeaks(threshold:int, path=BASE_DIR, feature=FEATURE):
    input_file = path / f"{feature}_multiinter.bed"
    output_file = path / f"{feature}_consensus.bed"
    command = command = (
        f"awk -v thresh={threshold} '$4 >= thresh {{print $1, $2, $3, $4}}' "
        f"OFS='\\t' {input_file} > {output_file}"
    )
    subprocess.run(command, shell=True, check=True)

def mergeAdjacentPeaks(path=BASE_DIR, feature=FEATURE):
    input_file = path / f"{feature}_consensus.bed"
    output_file = path / f"{feature}_consensus_merged.bed"
    command = f"sort -k1,1 -k2,2n {input_file} | bedtools merge > {output_file}"
    subprocess.run(command, shell=True, check=True)

def peakCenters(path=BASE_DIR, feature=FEATURE):
    input_file = path / f"{feature}_consensus_merged.bed"
    output_file = path / f"{feature}_center.bed"
    command = (
        f"awk 'BEGIN{{OFS=\"\\t\"}} "
        f"{{mid=int(($2+$3)/2); print $1,mid,mid+1}}' "
        f"{input_file} > {output_file}"
    )
    subprocess.run(command, shell=True, check=True)

# This function does the following for a Histone Mark
# 1. Computes the intersections of all narrow
# 2. Counts all the narrowPeak files in the dir
# 3. Filter Peaks based on THRESHOLD
# 4. Merge Adjacent Peaks
# 5. Create Peak Centers

print(f"Processing {FEATURE} at {BASE_DIR}")

cnt = countFiles()  # Gets the total # of profiles
print(f"{cnt} narrowPeak Files")

if cnt == 1:
    print("Single profile detected. Using streamlined path.")
    # Identify the single file
    single_file = list(BASE_DIR.glob("*.narrowPeak"))[0]
    
    # [1 & 2] multiinter & filter: Just copy the original to the consensus name
    # We add a 4th column of '1' to match multiinter format if it's missing
    output_consensus = BASE_DIR / f"{FEATURE}_consensus.bed"
    subprocess.run(f"awk 'BEGIN{{OFS=\"\\t\"}} {{print $1,$2,$3,1}}' {single_file} > {output_consensus}", shell=True)
    
    # [4] Merge (Still good practice to ensure sorted/merged)
    mergeAdjacentPeaks()
    
    # [5] Create Peak Centers
    peakCenters()

else:
    # Get all intervals with atleast 1 peak
    print("[1] Computing Intersections")
    computeIntersections() 

    # Gets the threshold value for Majority 50%
    print("[2] Computing Threshold")
    th = computeThreshold(cnt)
    print(f"Setting MAJORITY threshold to: {th}")

    # Get only intervals that is >= to Threshold
    print("[3] Filter Peaks based on THRESHOLD")
    filterPeaks(threshold=th)

    # Merge adjacent Peaks
    print("[4] Merge Adjacent Peaks")
    mergeAdjacentPeaks()

    # Compute center for each peak (for dist compute)
    print("[5] Create Peak Centers")
    peakCenters()
