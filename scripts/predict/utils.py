from ..utils import SequenceHandler


def extract_seq(
    chromosome: SequenceHandler, alt_base:str, position: int, length: int, is_zero_based: bool = True
):
    """Extract the Ref and Alt Sequences from a Chromosome.

    Args:
        chromosome (SequenceHandler): The Chromosome where the sequences would be taken from.
        alt_base (str): The Alt Base to be used.
        position (int): The Position of the Variant within the Chromosome.
        length (int): The Length of the Sequences to be output.
        is_zero_based (bool, optional): Whether indexing is zero-based on one-based. Defaults to True.

    Raises:
        ValueError: If Alt Base is not a single base
        ValueError: Given the position and length, if the start and end positions exceed the chromosome sequence's boundaries.

    Returns:
        dict: contains the reference and alt sequences and more.
    """
    # Get the Position of the Variant
    variant_pos = position if is_zero_based else position-1 # If 1-index, change behavior
    
    # Get Positions within the Output Sequences
    center_pos = length // 2    # Half-way point
    start_pos = variant_pos - center_pos
    end_pos = start_pos + length
    
    # Validate if alt_base is more than 1 base
    if len(alt_base) != 1:
        raise ValueError(f"Alt Base {alt_base} should be 1 base")
    
    # Validate if close to chromosome boundary
    if start_pos < 0 or end_pos > len(chromosome.sequence):
        raise ValueError(f"Variant at {position} too close to chromosome boundary")
    
    ref_seq = chromosome.sequence[start_pos:end_pos]
    alt_seq = ref_seq[:center_pos] + alt_base + ref_seq[center_pos+1:]
    
    # Format output
    return {
        # Location Info
        "position": position,
        "start": start_pos,
        "end": end_pos,
        
        # Sequence Info
        "ref_seq": str(ref_seq),
        "alt_seq": str(alt_seq),
        "ref_base": ref_seq[center_pos],
        "alt_base": alt_seq[center_pos],
        
        # Supplementary Info
        "left_cnt": center_pos,
        "right_cnt": len(ref_seq) - center_pos - 1
    }
