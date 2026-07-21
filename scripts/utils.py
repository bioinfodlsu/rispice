import scripts.helper as helper
import scripts.constants as constants

import pyBigWig
import pickle
import itertools
import pandas as pd
import numpy as np
import math
import torch
import scipy.linalg as la

from Bio import SeqIO
from Bio.Seq import Seq
from pathlib import Path
from collections import Counter
from datasets import Dataset
from transformers import DataCollatorForLanguageModeling
from torch.nn.functional import cross_entropy
from torch.utils.data import TensorDataset, DataLoader
from tqdm import tqdm
from typing import List, Tuple
from sklearn.model_selection import train_test_split


class AnnotationHandler:
    def __init__(self, annotation_type, db_file_path):
        self.type = annotation_type
        self.samples = helper.importCSV(db_file_path)

    def get_samples_of_study(
        self, study_name, should_update_samples_list=False, study_col_name="Study"
    ):
        """
        Get filtered samples based on the Study column
        """
        filtered = self.samples[self.samples[study_col_name] == study_name].reset_index(
            drop=True
        )

        if should_update_samples_list:
            self.samples = filtered

        return filtered

    def get_samples_of_annotation(
        self, annotation, annotation_col, should_update_samples_list=False
    ):
        """
        Get filtered samples based on the Annotation column
        """
        filtered = self.samples[self.samples[annotation_col] == annotation].reset_index(
            drop=True
        )

        if should_update_samples_list:
            self.samples = filtered

        return filtered

    def get_samples_of_tissue(
        self, tissue, should_update_samples_list=False, tissue_col_name="Tissue"
    ):
        """
        Get filtered samples based on the Study column
        """
        filtered = self.samples[self.samples[tissue_col_name] == tissue].reset_index(
            drop=True
        )

        if should_update_samples_list:
            self.samples = filtered

        return filtered

    def get_list_of_paths(self, path_col_name="Path"):
        """
        Returns a list of paths given the current samples df
        """
        return self.samples[path_col_name]


class SampleUtils:
    def get_chrom_lengths(sample_path):
        """
        Get lengths for each Chromosome within the sample (.bw)
        """
        bw = pyBigWig.open(sample_path)
        chroms = bw.chroms()
        bw.close()
        return chroms

    def getIntervals(sample_path, chrom_id, start, end, threshold=None):
        """Get the intervals with values via pyBigWig. Optional: specify a threshold"""
        bw = pyBigWig.open(sample_path)
        intervals = bw.intervals(chrom_id, start, end)
        bw.close()

        if threshold is None:
            return intervals

        # Filter interval list to only containing scores > threshold
        return [iv for iv in intervals if iv[2] > threshold]

    def getValues(sample_path, chrom_id, start, end):
        """Get the values within a range via pyBigWig"""
        bw = pyBigWig.open(sample_path)
        values = bw.values(chrom_id, start, end)
        bw.close()
        return values

    def getStats(sample_path, chrom_id, start, end, types=None):
        """Get the stats within a range via pyBigWig"""
        if types is None:
            types = ["mean", "min", "max", "std", "coverage"]

        bw = pyBigWig.open(sample_path)
        stats = {}

        for type in types:
            stats[type] = bw.stats(chrom_id, start, end, type=type)[0]

        bw.close()
        return stats

    def loadSampleNumpy(paths: List[str], shuffle=False, count: int = -1) -> List[str]:
        """Load sample data from a .npy file.

        Args:
            paths (List[str]): relative paths to the numpy files
            shuffle (bool, optional): should shuffle before extraction. Defaults to False.
            count (int, optional): the number of data to retrieve. Defaults to -1.

        Returns:
            List[str]: a list of all samples
        """
        sample_list = []
        for path in paths:
            data = np.load(path)
            data = data.astype(str).tolist()

            # Should shuffle the samples
            if shuffle:
                np.random.shuffle(data)

            # Check if you need to get everything
            if count != -1:
                data = data[:count]

            sample_list.extend(data)

        return sample_list

    def loadTrainValNumpy(
        paths: List[str],
        val_pct=constants.VALIDATION_PCT,
        shuffle=False,
        count: int = -1,
    ) -> Tuple[List[str], List[str]]:
        """Load sample data from .npy files and split into Train and Validation sets.

        Args:
            paths (List[str]): relative paths to the numpy files
            val_pct (float): Fraction for validation split (e.g., 0.2 for 80/20).
            shuffle (bool, optional): should shuffle when splitting. Defaults to False.
            count (int, optional): the number of data to retrieve per file (before splitting). Defaults to -1.

        Returns:
            Tuple[List[str], List[str]]: (train_set, val_set)
        """
        all_train = []
        all_val = []

        # Iterate files and split each of them based on val_pct
        for path in paths:
            data = np.load(path)
            data = data.astype(str).tolist()

            # Check if you need to get everything
            if count != -1:
                data = data[:count]

            # Split via sklearn. Shuffle if needed
            train_set, val_set = train_test_split(
                data, test_size=val_pct, shuffle=shuffle, random_state=42
            )

            all_train.extend(train_set)
            all_val.extend(val_set)

        return all_train, all_val


class SequenceHandler:
    def __init__(
        self,
        id,
        name,
        description,
        sequence,
        start_index=0,
        end_index=None,
        is_complement=False,
    ):
        self.id: str = id
        self.name: str = name
        self.description: str = description
        self.sequence: Seq = sequence

        # Additional Details
        self.start_index: int = start_index
        if end_index is None:
            self.end_index: int = len(sequence) - 1
        else:
            self.end_index: int = end_index

        self.is_complement: bool = is_complement

    def getKmers(self, k):
        """Return a list of K-mers based on the sequence"""
        return [
            str(self.sequence[i : i + k]) for i in range(len(self.sequence) - k + 1)
        ]

    def divideToBins(self, bin_size: int, stride: int) -> List["SequenceHandler"]:
        """Divides the sequence into multiple SequenceHandler instances given bin_size."""
        bins = []
        for i in range(0, len(self.sequence), stride):
            id = len(bins) + 1
            subseq = self.sequence[i : i + bin_size]

            # Pad with N if shorter than bin_size
            actual_len = len(subseq)
            if actual_len < bin_size:
                pad_len = bin_size - actual_len
                subseq = subseq + Seq("N" * pad_len)
            else:
                pad_len = 0

            # true end index in the original sequence (inclusive)
            real_end_index = min(i + bin_size - 1, len(self.sequence) - 1)

            description = f"{self.name} Bin#{id:,} (size={actual_len}"
            if pad_len:
                description += f" + padded {str(pad_len)})."
            else:
                description += ")."

            bins.append(
                SequenceHandler(
                    id,
                    f"{self.name}:{i:_}-{real_end_index:_}",
                    description,
                    Seq(subseq),
                    start_index=i,
                    end_index=real_end_index,
                )
            )

        return bins

    def extendSequence(self, ref_seq: Seq, extension_size: int, update_end_index:bool = True) -> "SequenceHandler":
        """Appends an extension to the current sequence given the extension size"""
        expected_size = len(self.sequence) + extension_size

        start = self.end_index + 1  # Next index from the current bin
        end = start + extension_size

        extension_seq = ref_seq[start:end]
        extended_seq = self.sequence + extension_seq

        if len(extended_seq) < expected_size:
            extended_seq = extended_seq + Seq("N" * (expected_size - len(extended_seq)))

        # true end index in the original sequence (inclusive)
        real_end_index = min(end - 1, len(ref_seq) - 1)

        # Save to current instance
        self.sequence = extended_seq
        
        if update_end_index:
            self.end_index = real_end_index  # End is inclusive

        actual_added = len(extension_seq)
        padded = extension_size - actual_added

        if padded > 0:
            self.description += (
                f" Extended by {actual_added}bp forward (+{padded}bp padded with N)."
            )
        else:
            self.description += f" Extended by {extension_size}bp forward."

        return self
    
    def extendSequenceBackward(self, ref_seq: Seq, extension_size: int, update_start_index:bool = True):
        """Prepends an extension to the current sequence given the extension size"""
        end = self.start_index - 1              # one-bp away from the start index
        start = end - extension_size
        
        if start < 0:
            n_padding = Seq("N" * abs(start))
            ref_part = ref_seq[max(0, start):end]
            extension_seq = n_padding + ref_part
        else:
            extension_seq = ref_seq[start:end]
        
        # Save to current instance
        self.sequence = extension_seq + self.sequence
        
        if update_start_index:
            self.start_index = 0 if start < 0 else start
        
        self.description += f" Extended by {extension_size}bp backwards."
        return self

    def duplicate(self, count=1, description=" Duplicate.") -> "SequenceHandler":
        return SequenceHandler(
            id=f"{self.id}_{count}",
            name=f"{self.name} {description}",
            description=f"{self.description} {description}",
            sequence=self.sequence,
            start_index=self.start_index,
            end_index=self.end_index,
        )

    def convertToComplement(self) -> "SequenceHandler":
        """Convert the instance's sequence into its complement."""
        self.is_complement = not self.is_complement
        self.sequence = self.sequence.complement()
        return self

    def __repr__(self):
        id_ref = f"[{self.id}]"
        len_ref = f"[{len(self.sequence):_}bp]"
        bases_ref = f"[Bases {self.start_index+1:_} to {self.end_index+1:_}]"
        return f"{id_ref}{len_ref}{bases_ref} {self.description}"


class SequenceUtils:
    def getSequences(path, filter_with_id=[]) -> List[SequenceHandler]:
        """Uses Biopython's SeqIO to parse the fasta file. Returns list of sequences."""
        seq = []
        for record in SeqIO.parse(path, "fasta"):
            if record.id not in filter_with_id:
                continue

            seq.append(
                SequenceHandler(
                    id=record.id,
                    name=record.name,
                    description=record.description,
                    sequence=record.seq.upper(),
                )
            )

        return seq

    def saveKmerList(kmer_list, path, file_name):
        """Given a list of Kmers, save it as a Pickle"""
        directory_path = CommonUtils.createPathIfNotExist(path)

        # Ensure extension
        if not file_name.endswith(".pkl"):
            file_name = f"{file_name}.pkl"

        path_to_file = directory_path / file_name

        # Check if File Already Exists
        file_exists = CommonUtils.doesFileExist(str(path_to_file))

        with open(path_to_file, "wb") as file:
            pickle.dump(kmer_list, file)

        if file_exists:
            print(f"The file {path_to_file} is overwritten.")
        else:
            print(f"The file {path_to_file} is created.")

    def loadKmerList(path_to_file):
        """Given a path to a kmer_list, load the existing Pickle file."""
        if not path_to_file.endswith(".pkl"):
            path_to_file = f"{path_to_file}.pkl"

        file_exists = CommonUtils.doesFileExist(str(path_to_file))
        if not file_exists:
            print(f"The file {path_to_file} does not exist.")
            return

        with open(path_to_file, "rb") as file:
            loaded_obj = pickle.load(file)

        print(f"The file {path_to_file} loaded successfully.")

        return loaded_obj

    def getChrNum(seq_id):
        """Returns the Chromosome given the SeqID"""
        if seq_id not in constants.NIPPONBARE_ID_TO_CHR:
            print(f"{seq_id} not in Nipponbare ID reference. Check constants.")
            return

        return constants.NIPPONBARE_ID_TO_CHR[seq_id]

    def duplicateAndComplementBins(
        bins: List["SequenceHandler"],
    ) -> List["SequenceHandler"]:
        """For every bin, duplicate it and turn it into its complement seq."""
        result = []
        for bin in bins:
            complement = bin.duplicate(" For Complement.").convertToComplement()
            result.append(complement)

        return result

    def extendBins(
        bins: List["SequenceHandler"], ref_seq: Seq, extension_size: int, update_index: bool = True
    ) -> List["SequenceHandler"]:
        """For every bin, extend the sequence forwards X-bp within the reference genome."""
        for bin in bins:
            bin.extendSequence(ref_seq, extension_size, update_index)

    def extendBinsBackward(
        bins: List["SequenceHandler"], ref_seq: Seq, extension_size: int, update_index: bool = True
    ) -> List["SequenceHandler"]:
        """For every bin, extend the sequence backward X-bp within the reference genome."""
        for bin in bins:
            bin.extendSequenceBackward(ref_seq, extension_size, update_index)

    def getSeqStrings(sequences: List["SequenceHandler"]) -> List[str]:
        """Given a list of SequenceHandlers, get all sequence in str format."""
        seq_strings = []
        for seq in sequences:
            seq_strings.append(str(seq.sequence))
        return seq_strings

    def filterAmbiguity(
        sequences: List["SequenceHandler"], threshold: float
    ) -> List["SequenceHandler"]:
        """Remove all sequences where its % of ambiguous nucleotides are above the threshold"""
        filtered_seq = []
        for seq in sequences:
            ambiguous_pct = SequenceUtils.countAmbiguous(str(seq.sequence))

            # Only add to filtered list if threshold is still higher
            if threshold >= ambiguous_pct:
                filtered_seq.append(seq)

        return filtered_seq

    def countAmbiguous(seq: str) -> float:
        """Return the percentage of ambiguous nucleotides (e.g., N) in a sequence."""
        seq = seq.upper()
        if len(seq) == 0:
            return 0.0
        n_count = seq.count("N")
        return (n_count / len(seq)) * 100


class ExploratoryUtils:
    def getKMerCounts(kmer_list, vocab):
        """Counts the # of instances per unique kmer."""
        counts = Counter(kmer_list)
        counts = {kmer: counts.get(kmer, 0) for kmer in vocab}
        return counts

    def getKmerCombinations(K, alphabet=["A", "C", "G", "T", "N"]):
        return ["".join(p) for p in itertools.product(alphabet, repeat=K)]

    def saveDataFrame(df, path):
        """Given a df, save it to a file."""
        # Create the directory if not exist
        CommonUtils.createPathIfNotExist(str(Path(path).parent))

        df.to_csv(path, index=False)


class CommonUtils:
    def createPathIfNotExist(path):
        """Creates the dirs of a path. Returns `Path` object"""
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj

    def doesFileExist(path_to_file):
        """Returns true if the file exists"""
        return Path(path_to_file).is_file()

    def readCsvColToList(path_to_file, col_index=0):
        """Reads a csv file, and returns a list."""
        df = pd.read_csv(path_to_file)
        return df.iloc[:,0].tolist()

    def saveToPickle(path: Path, filename: str, data, overwrite=True):
        path_to_file = path / f"{filename}.pkl"

        doesExist = CommonUtils.doesFileExist(path_to_file)

        if (not overwrite) and doesExist:
            print(f"{path_to_file} already exists. Skipping")
            return

        with open(path_to_file, "wb") as f:
            pickle.dump(data, f)

        if overwrite and doesExist:
            print(f"Overwritten {path_to_file}")
        else:
            print(f"Saved {path_to_file}")

    def loadPickle(file_path: str):
        """Load a Pickle file"""
        try:
            with open(file_path, "rb") as file:
                loaded_data = pickle.load(file)
            print("Successfully loaded data from:", file_path)
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
        except Exception as e:
            print(f"An error occurred while loading the pickle file: {e}")

        return loaded_data

    def saveToPickleBatched(path: Path, filename: str, data, batch_size=50000):
        """Save batched pickles."""
        path.mkdir(parents=True, exist_ok=True)
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            batch_file = path / f"{filename}_part{i//batch_size}.pkl"
            with open(batch_file, "wb") as f:
                pickle.dump(batch, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"Saved {batch_file}")
            
    def getFilesFromFolder(folder_path:str) -> List[str]:
        """Given a path to a folder, return the list of files."""
        folder = Path(folder_path)
        files = [str(f) for f in folder.iterdir() if f.is_file()]
        return files


class PreTrainingUtils:
    def performMasking(
        data: torch.Tensor,
        ignore_ids: torch.Tensor,
        mask_token_id: int,
        vocab_size: int,
        mask_pct: float = 0.15,
        mask_dist: tuple = (0.8, 0.1, 0.1),
    ):
        """Perform a Masking Procedure on a set of data (already encoded).

        Args:
            data (torch.Tensor): data to be masked (input_ids)
            ignore_ids (torch.Tensor): special ids to be ignored for masking
            mask_token_id (int): specific token for MASK
            vocab_size (int): vocab size of the tokenizer
            mask_pct (float, optional): MLM Percentage. Defaults to 0.15.
            mask_dist (tuple, optional): Out of the MLM Percent,
                how many would be masked, randomized, and unchanged respectively.
                Defaults to (0.8, 0.1, 0.1).

        Returns:
            masked_data (torch.Tensor): Input tensor with masks/random tokens applied.
            labels (torch.Tensor): Label tensor where only masked tokens retain original IDs, others are -100.
        """
        # Get randomized values between 0 and 1 for each entry in data
        rand = torch.rand(data.shape, device=data.device)
        # Create a tensor on whether to mask a token or not
        mask_arr = (rand < mask_pct) & (~torch.isin(data, ignore_ids))

        # From the 15%, divide into 80-10-10
        mask_indices = torch.nonzero(mask_arr, as_tuple=True)
        num_to_mask = mask_indices[0].numel()  # Get total count to mask

        # Shuffle the indeces to be masked
        perm = torch.randperm(num_to_mask, device=data.device)
        n_mask = int(mask_dist[0] * num_to_mask)  # Get the 80% of num to mask
        n_rand = int(mask_dist[1] * num_to_mask)  # Get the 10% of num to mask

        # Get Tensor for those indeces to be masked, randomized, unchanged
        mask_mask = perm[:n_mask]
        rand_mask = perm[n_mask : n_mask + n_rand]
        # unchanged_mask = perm[n_mask + n_rand:]

        # Performing Masking
        masked_data = data.clone()  # Create copy of data
        labels = torch.full_like(data, -100)  # Create label tensor

        # Mask the Tokens
        row = mask_indices[0][mask_mask]
        col = mask_indices[1][mask_mask]
        labels[row, col] = data[row, col]  # Store original labels in label tensor
        masked_data[row, col] = mask_token_id  # Replace those data with [MASK]

        # Randomize the Tokens
        row = mask_indices[0][rand_mask]
        col = mask_indices[1][rand_mask]
        labels[row, col] = data[row, col]  # Store original labels in label tensor
        masked_data[row, col] = torch.randint(
            low=0, high=vocab_size, size=(n_rand,), device=data.device
        )  # Get a random int from 0 to VOCAB_SIZE

        return masked_data, labels

    def kmerize(seq: str, k: int = 6, max_kmers: int = None):
        kmers = [seq[i:i+k] for i in range(len(seq) - k + 1)]
        if max_kmers is not None:
            kmers = kmers[:max_kmers]
        return " ".join(kmers)

    def prepare_dataset(
        data: torch.Tensor,
        tokenizer,
        batch_size=constants.BATCH_SIZE,
        max_length=constants.MAX_LENGTH,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    ) -> DataLoader:
        # Encode Data
        encoded_data = tokenizer(
            data,
            return_tensors="pt",
            truncation=True,
            padding="max_length",
            max_length=max_length,
        )

        # Retrieve Inputs and Labels
        input_ids = encoded_data["input_ids"].squeeze()

        special_ids = torch.tensor(tokenizer.all_special_ids, device=device)
        input_ids = input_ids.to(device)

        masked_inputs, labels = PreTrainingUtils.performMasking(
            data=input_ids,
            ignore_ids=special_ids,
            mask_token_id=tokenizer.mask_token_id,
            vocab_size=tokenizer.vocab_size,
        )

        # Get Attention Mask
        attention_mask = encoded_data["attention_mask"].squeeze()
        attention_mask = attention_mask.to(device)

        # Return DataLoader
        return DataLoader(
            TensorDataset(masked_inputs, attention_mask, labels),
            batch_size=batch_size,
            shuffle=True,
        )

    def computeAccuracy(labels, logits):
        """Compute Accuracy for MLM"""
        mask_arr = (labels != -100).contiguous()  # Get the indices that was masked
        preds = logits.argmax(-1)  # Get the highest-scoring token along vocab-size

        # Defensive checks
        if preds.shape != labels.shape:
            raise ValueError(f"Shape mismatch: preds {preds.shape}, labels {labels.shape}")
        if labels.max() >= logits.size(-1):
            raise ValueError(f"Invalid label id {labels.max().item()} >= vocab_size {logits.size(-1)}")

        correct = (preds[mask_arr] == labels[mask_arr]).sum().item()
        total = mask_arr.sum().item()
        return correct / total if total > 0 else 0.0

    def mlm_prep(data: List[str], tokenizer) -> DataLoader:
        """Prep for Masked Language Modeling via `DataCollatorForLanguageModeling` of **HuggingFace**"""
        encoded_data = tokenizer(
            data,
            return_tensors="pt",
            truncation=True,
            padding="max_length",
            max_length=constants.MAX_LENGTH,
        )
        dataset = Dataset.from_dict(encoded_data)
        
        # MLM Collator
        collate_fn = DataCollatorForLanguageModeling(
            tokenizer,
            mlm=True,
            mlm_probability=constants.MASKED_PCT,
            return_tensors="pt",
        )

        # Create DataLoader
        return DataLoader(
            dataset,
            batch_size=constants.BATCH_SIZE,
            collate_fn=collate_fn,
            shuffle=True,
        )

    def evaluate(
        model,
        dataloader,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    ):
        """Perform evaluation of a Model for Masked Language Modeling"""
        model.eval()
        model = model.to(device)

        # --- Perform Evaluation ----
        total_loss = 0.0
        total_acc = 0.0
        count = 0

        with torch.no_grad():
            for batch in tqdm(dataloader, desc="Evaluate", unit="batch"):
                # Transfer batch to GPU
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch["labels"].to(device)

                # Forward Masked Input to Model
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                logits = outputs.logits

                # Flatten predictions and targets for CrossEntropyLoss
                vocab_size = logits.size(-1)
                logits_flat = logits.view(-1, vocab_size)
                labels_flat = labels.view(-1)

                # Compute masked-token loss
                loss = cross_entropy(logits_flat, labels_flat, ignore_index=-100)

                # Masked accuracy
                total_acc += PreTrainingUtils.computeAccuracy(labels, logits)

                total_loss += loss.item()
                count += 1

        avg_loss = total_loss / count
        perplexity = math.exp(avg_loss)
        avg_acc = total_acc / count

        return avg_loss, avg_acc, perplexity

    def train(
        model,
        optimizer,
        dataloader,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    ):
        """Train a Model (for one epoch) for Masked Language Modeling"""
        model.train()
        model = model.to(device)

        # --- Perform Training ----
        total_loss = 0.0
        total_acc = 0.0
        count = 0

        scaler = torch.amp.GradScaler(device.type)

        for batch in tqdm(dataloader, desc="Training", unit="batch"):
            # Transfer batch to GPU
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            # Zero grad the optimizer
            optimizer.zero_grad(set_to_none=True)

            # Forward Masked Input to Model
            with torch.amp.autocast(device.type):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits

                # Flatten predictions and targets for CrossEntropyLoss
                vocab_size = logits.size(-1)
                logits_flat = logits.view(
                    -1, vocab_size
                )  # Input:  (batch_size*seq_len, vocab_size)
                labels_flat = labels.view(-1)  # Target: (batch_size*seq_len)

                # Compute masked-token loss
                loss = cross_entropy(logits_flat, labels_flat, ignore_index=-100)

            # Backward pass
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            # Masked accuracy
            total_acc += PreTrainingUtils.computeAccuracy(labels, logits)

            total_loss += loss.item()
            count += 1

        # Compute total stats
        avg_loss = total_loss / count
        perplexity = math.exp(avg_loss)
        avg_acc = total_acc / count

        return avg_loss, avg_acc, perplexity

    def train_model(
        model,
        tokenizer,
        train_data,
        val_data,
        optimizer,
        epochs=constants.EPOCHS,
        patience=constants.EARLY_STOP_PATIENCE,
    ):
        """Conduct the training for the model."""
        best_val_loss = float("inf")
        patience_ctr = 0

        for epoch in range(epochs):
            print(f"\nEpoch {epoch+1}/{epochs}")

            train_loss, train_acc, train_ppl = PreTrainingUtils.train(
                model, tokenizer, train_data, optimizer
            )

            val_loss, val_acc, val_ppl = PreTrainingUtils.evaluate(
                model, tokenizer, val_data
            )

            print(
                f"Train | Loss: {train_loss:.4f} | Acc: {train_acc:.4f} | PPL: {train_ppl:.4f}"
            )
            print(
                f"Valid | Loss: {val_loss:.4f} | Acc: {val_acc:.4f} | PPL: {val_ppl:.4f}"
            )

            # ---- Early Stopping ----
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_ctr = 0
                best_model_state = model.state_dict()
            else:
                patience_ctr += 1
                if patience_ctr >= patience:
                    print("Early stopping triggered.")
                    break

        # Load best model (optional)
        model.load_state_dict(best_model_state)
        return model

class MultitestUtils:
    def compute_effective_m(ld_matrix):
        """
        Computes the effective number of independent tests (M_eff) from an LD matrix
        using the Li and Ji Method.
        """
        ld_matrix = np.asarray(ld_matrix)
        
        ld_matrix_clean = np.nan_to_num(ld_matrix, nan=0.0, posinf=1.0, neginf=-1.0)
        
        # Get the eigenvalues
        # eigenvalues = np.linalg.eigvalsh(ld_matrix)
        try:
            eigenvalues = la.eigvalsh(ld_matrix_clean)
        except la.LinAlgError:
            # Emergency Fallback: If it still fails, slightly perturb the diagonal (ridge regression style)
            # This breaks perfect collinearity dependencies
            print("Warning: Standard convergence failed. Applying ridge perturbation (1e-6)...")
            perturbed_ld = ld_matrix_clean + np.eye(ld_matrix_clean.shape[0]) * 1e-6
            eigenvalues = la.eigvalsh(perturbed_ld)
        
        # Take absolute values of eigenvals |lambda|
        x = np.abs(eigenvalues)
        
        # 4. Implement f(x) = I(x >= 1) + (x - floor(x))
        part_1 = (x >= 1).astype(float)
        part_2 = x - np.floor(x)
        f_x = part_1 + part_2
        
        m_eff_raw = np.sum(f_x)
        m_eff = max(1, int(np.round(m_eff_raw)))
        
        print(f"-> Effective independent tests (M_eff): {m_eff}")
        return m_eff

    def bh(input_df, q, m, p_col="p-value"):
        df = input_df.copy()
        df.sort_values(by=p_col, inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Rank p-values
        df["rank"] = df.index + 1
        
        # Compute the formal BH threshold: (k / m) * q
        df["bh_threshold"] = (df["rank"] / m) * q
        
        # Find the indexes where the condition P_(k) <= (k / m) * q is satisfied
        sig_indexes = df[df['p-value'] <= df['bh_threshold']].index
        
        if len(sig_indexes) > 0:
            # The largest index (highest rank k) that met the criteria
            max_sig_idx = sig_indexes.max()
            
            # Mark everything up to (and including) this index as significant
            df['significant'] = df.index <= max_sig_idx
        else:
            df['significant'] = False
        
        print(f"Number of SNPs that survived BH: {np.sum(df['significant'] )}")
        return df, None # there's no adjusted alpha

    def bh_meff(input_df, q, m_eff, p_col="p-value"):
        """
        Modified Benjamini-Hochberg (step-up) procedure incorporating the 
        effective number of independent tests (M_eff) to account for correlation.
        """
        df = input_df.copy()
        df.sort_values(by=p_col, inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Rank p-values
        df["rank"] = df.index + 1
        
        # =========================================================================
        # FORMULA ANNOTATION:
        # Threshold = [q / M_eff] + [ (i - 1) / (M - 1) ] * [ q - (q / M_eff) ]
        #
        #   * q / m_eff       : The starting value of the sequence (EWSL threshold)
        #   * (i-1) / (m-1)   : The step coefficient scale (0 when i=1, 1 when i=M)
        #   * q               : The final controlled FDR rate at the end of the sequence
        #   * q - (q / m_eff) : The overall span/range of the sequence
        # =========================================================================
        start_term = q / m_eff
        step_multiplier = (df["rank"] - 1) / (len(df) - 1)
        span_term = q - (q / m_eff)
        
        # Compute the formal Meff-based threshold
        df["bh_threshold"] = start_term + (step_multiplier * span_term)
        
        # Find the indexes where the condition P_(k) <= (k / m) * q is satisfied
        sig_indexes = df[df[p_col] <= df['bh_threshold']].index
        
        if len(sig_indexes) > 0:
            # The largest index (highest rank k) that met the criteria
            max_sig_idx = sig_indexes.max()
            
            # Reject H_(1), ..., H_(k) (mark everything up to and including 'k' as significant)
            df['significant'] = df.index <= max_sig_idx
        else:
            df['significant'] = False
        
        print(f"Number of SNPs that survived BH_Meff: {np.sum(df['significant'] )}")
        return df, None # there's no adjusted alpha

    def bonferroni(input_df, q, m, p_col="p-value"):
        """Implementation of Bonferroni"""
        df = input_df.copy()
        
        # Bonferroni formula for adjusted alpha
        adjusted_alpha = q / m
        
        # Compute adjusted-p for ref
        df["p_bonferroni"] = df[p_col] * m
        df["p_bonferroni"] = np.minimum(df["p_bonferroni"], 1.0)
        
        # Check significance based on adjusted alpha
        df["significant"] = df[p_col] <= adjusted_alpha
        
        print(f"Adjusted Alpha (from {q}): {adjusted_alpha}")
        print(f"Number of SNPs that survived Adjusted Bonferroni: {np.sum(df['significant'] )}")
        return df, adjusted_alpha

    def sidak(input_df, q, m, p_col="p-value"):
        """Implementation of Sidak"""
        df = input_df.copy()
        
        # Sidak formula for adjusted alpha
        adjusted_alpha = 1 - (1 - q) ** (1/m)
        
        # Compute adjusted-p for ref
        df["p_sidak"] = 1 - (1 - df[p_col]) ** m
        
        # Check significance based on adjusted alpha
        df["significant"] = df[p_col] <= adjusted_alpha
        
        print(f"Adjusted Alpha (from {q}): {adjusted_alpha}")
        print(f"Number of SNPs that survived Adjusted Sidak: {np.sum(df['significant'] )}")
        return df, adjusted_alpha
    
    def multitest(df, alpha, meff, show_n=3):
        """Helper function for executing all multitest results"""
        print_cols = ["id", "Variant", "p-value", "significant"]
        # BH_meff
        print("BH Meff")
        temp, _ = MultitestUtils.bh_meff(df, alpha, meff)
        print(temp[["id", "Variant", "p-value", "bh_threshold", "significant"]].head(show_n))

        # Bonferroni
        print("\nBonf")
        temp, _ = MultitestUtils.bonferroni(df, alpha, meff)
        print(temp[print_cols].head(show_n))

        # Sidak
        print("\nSidak")
        temp, _ = MultitestUtils.sidak(df, alpha, meff)
        print(temp[print_cols].head(show_n))