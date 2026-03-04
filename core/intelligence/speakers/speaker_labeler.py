"""
Speaker Labeler — Interactive: show sample phrases, ask user for speaker name.
Integrates with voice_registry for persistence.
"""
from typing import List, Dict, Optional


def label_unknown_speakers(segments: List[Dict], max_phrases: int = 8) -> Dict[str, str]:
    """
    For each unique anonymous speaker in segments, show sample phrases
    and prompt user for identification. Returns mapping {anon_id: name}.
    """
    from collections import defaultdict
    speaker_phrases = defaultdict(list)
    for seg in segments:
        spk = seg.get("speaker", "UNKNOWN")
        text = seg.get("text", "")
        if text and len(speaker_phrases[spk]) < max_phrases:
            speaker_phrases[spk].append(text[:120])

    mapping = {}
    unique_speakers = sorted(speaker_phrases.keys())
    total = len(unique_speakers)
    print(f"\n[speaker_labeler] {total} speaker(s) detected. Let's identify them.\n")

    for i, spk in enumerate(unique_speakers, 1):
        print(f"─── Speaker {i}/{total}: {spk} ───")
        phrases = speaker_phrases[spk]
        if phrases:
            print("Sample phrases:")
            for j, p in enumerate(phrases[:max_phrases], 1):
                print(f"  {j}. {p}")
        else:
            print("  (no transcribed text available)")
        name = input(f"\nName for {spk} (or Enter to skip): ").strip()
        if name:
            mapping[spk] = name
        else:
            mapping[spk] = spk  # keep anonymous id
        print()

    return mapping


def apply_labels(segments: List[Dict], mapping: Dict[str, str]) -> List[Dict]:
    """Apply name mapping to segments."""
    labeled = []
    for seg in segments:
        new_seg = dict(seg)
        anon = seg.get("speaker", "UNKNOWN")
        new_seg["speaker"] = mapping.get(anon, anon)
        labeled.append(new_seg)
    return labeled
