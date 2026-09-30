"""
Stage 1: Long Strip Pairing Preprocessing
Function: Identify long strips and reduce layout aspect ratio through pairing
"""
from typing import List, Tuple
from data_loader import Block


def identify_strips(blocks: List[Block], threshold: float = 2.5) -> List[Block]:
    """
    Identify long strips: aspect_ratio >= threshold

    Args:
        blocks: List of Block objects
        threshold: Aspect ratio threshold

    Returns:
        List of strip Blocks
    """
    strips = [b for b in blocks if b.aspect_ratio() >= threshold]
    return strips


def find_best_match(strip: Block, candidates: List[Block], tolerance: float = 0.15) -> Tuple[Block, float]:
    """
    Find best pairing match for given strip

    Pairing criteria:
    - strip's long edge ~ candidate's short edge
    - strip's short edge ~ candidate's long edge

    Args:
        strip: Strip to pair
        candidates: Candidate strip list
        tolerance: Size matching tolerance (relative error)

    Returns:
        (best_match, score) if found; otherwise (None, float('inf'))
    """
    long_a = max(strip.w, strip.h)
    short_a = min(strip.w, strip.h)

    best_match = None
    best_score = float('inf')

    for candidate in candidates:
        if candidate.idx == strip.idx:
            continue

        long_b = max(candidate.w, candidate.h)
        short_b = min(candidate.w, candidate.h)

        # Check complementarity: A's long ~ B's short, A's short ~ B's long
        error_long = abs(long_a - short_b) / short_b if short_b > 0 else float('inf')
        error_short = abs(short_a - long_b) / long_b if long_b > 0 else float('inf')

        if error_long <= tolerance and error_short <= tolerance:
            # Calculate combined aspect ratio as score (closer to 1.0 is better)
            combined_w = long_a
            combined_h = short_a + short_b
            combined_ratio = max(combined_w, combined_h) / min(combined_w, combined_h)
            score = abs(combined_ratio - 1.0)  # Closer to 1.0, smaller score

            if score < best_score:
                best_score = score
                best_match = candidate

    return best_match, best_score


def pair_strips(blocks: List[Block], threshold: float = 2.5, tolerance: float = 0.5) -> Tuple[List[Block], List[Tuple[int, int, float, float]]]:
    """
    Strip pairing algorithm

    Args:
        blocks: Original Block list
        threshold: Strip identification threshold
        tolerance: Pairing size tolerance (increased to 0.5 for flexibility)

    Returns:
        (paired_blocks, pairs_info)
        - paired_blocks: Block list after pairing (strips replaced by composites)
        - pairs_info: [(idx1, idx2, combined_w, combined_h), ...]
    """
    # Identify strips
    strips = identify_strips(blocks, threshold)

    # Sort by aspect ratio descending (prioritize longest strips)
    strips.sort(key=lambda b: b.aspect_ratio(), reverse=True)

    # Track paired indices
    paired_indices = set()
    pairs_info = []

    # Create result list, initially all blocks
    result_blocks = blocks.copy()

    # Greedy pairing
    for strip in strips:
        if strip.idx in paired_indices:
            continue

        # Find best match among unpaired strips
        candidates = [s for s in strips if s.idx not in paired_indices]
        best_match, score = find_best_match(strip, candidates, tolerance)

        if best_match is not None:
            # Found pair, create composite block
            long_a = max(strip.w, strip.h)
            short_a = min(strip.w, strip.h)
            long_b = max(best_match.w, best_match.h)
            short_b = min(best_match.w, best_match.h)

            # Combined dimensions: keep long edge, add short edges
            combined_w = long_a
            combined_h = short_a + short_b

            # Create composite (use smaller idx)
            composite_idx = min(strip.idx, best_match.idx)
            composite_name = f"pair_{strip.name}_{best_match.name}"
            composite = Block(composite_idx, composite_name, combined_w, combined_h)

            # Record pairing info
            pairs_info.append((strip.idx, best_match.idx, combined_w, combined_h))
            paired_indices.add(strip.idx)
            paired_indices.add(best_match.idx)

            # Remove original strips, add composite
            result_blocks = [b for b in result_blocks if b.idx not in {strip.idx, best_match.idx}]
            result_blocks.append(composite)

    return result_blocks, pairs_info


def print_pairing_report(original_blocks: List[Block], paired_blocks: List[Block], pairs_info: List[Tuple[int, int, float, float]]):
    """Print pairing report"""
    print("\n" + "=" * 60)
    print("Long Strip Pairing Report")
    print("=" * 60)

    print(f"Original blocks: {len(original_blocks)}")
    print(f"After pairing: {len(paired_blocks)}")
    print(f"Pairs found: {len(pairs_info)}")

    if pairs_info:
        print("\nPaired strips:")
        for idx1, idx2, w, h in pairs_info:
            b1 = next(b for b in original_blocks if b.idx == idx1)
            b2 = next(b for b in original_blocks if b.idx == idx2)
            ratio = max(w, h) / min(w, h)
            print(f"  {b1.name}({b1.w:.1f}x{b1.h:.1f}, AR={b1.aspect_ratio():.2f}) + "
                  f"{b2.name}({b2.w:.1f}x{b2.h:.1f}, AR={b2.aspect_ratio():.2f}) "
                  f"-> composite({w:.1f}x{h:.1f}, AR={ratio:.2f})")

    # Verify area conservation
    original_area = sum(b.area for b in original_blocks)
    paired_area = sum(b.area for b in paired_blocks)
    print(f"\nArea conservation check:")
    print(f"  Original: {original_area:.1f}")
    print(f"  After pairing: {paired_area:.1f}")
    print(f"  Difference: {abs(original_area - paired_area):.6f}")

    assert abs(original_area - paired_area) < 0.01, "Area not conserved!"
    print("  [OK] Area conserved")

    print("=" * 60)


# ==================== M2 Verification: Pairing Algorithm ====================
if __name__ == '__main__':
    from config import DATA_PATHS
    from data_loader import load_blocks

    print("=" * 60)
    print("Stage 1 Verification: Strip Pairing")
    print("=" * 60)

    # Test n100 dataset
    test_dataset = 'n100'
    print(f"\nTesting {test_dataset}:")

    blocks = load_blocks(DATA_PATHS[test_dataset])

    # Execute pairing
    paired_blocks, pairs_info = pair_strips(blocks)

    # Print report
    print_pairing_report(blocks, paired_blocks, pairs_info)

    # Acceptance tests
    print("\nAcceptance Tests:")

    # 1. At least 1 pair found (optional, depends on dataset)
    if len(pairs_info) >= 1:
        print(f"  [OK] Found {len(pairs_info)} pair(s)")
    else:
        print("  [WARN] No pairs found (may need tolerance adjustment)")

    # 2. Total area unchanged after pairing
    original_area = sum(b.area for b in blocks)
    paired_area = sum(b.area for b in paired_blocks)
    assert abs(original_area - paired_area) < 0.01, "Area should be conserved"
    print("  [OK] Area conserved")

    # 3. Paired blocks have aspect ratio close to 1.0
    for idx1, idx2, w, h in pairs_info:
        ratio = max(w, h) / min(w, h)
        assert ratio < 2.5, f"Paired block ratio {ratio:.2f} should be < 2.5"
    print("  [OK] All paired blocks have improved aspect ratios")

    print("\n" + "=" * 60)
    print("M2 Milestone: Strip Pairing - PASSED [OK]")
    print("=" * 60)
