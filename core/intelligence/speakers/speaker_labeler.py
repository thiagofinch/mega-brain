"""
Speaker Labeler — Interactive: show sample phrases, ask user for speaker name.
Integrates with voice_registry for persistence.
"""


def label_unknown_speakers(
    segments: list[dict],
    max_phrases: int = 6,
    phrase_len: int = 220,
    expected_speakers: int | None = None,
) -> dict[str, str]:
    """
    For each unique anonymous speaker in segments, show sample phrases
    and prompt user for identification. Returns mapping {anon_id: name}.

    Includes a verification step: after showing detected speakers, asks
    the user if the count looks right before proceeding to labeling.
    This catches cases where the diarizer merged distinct voices.
    """
    from collections import defaultdict

    # Collect stats and phrases per speaker
    speaker_phrases: dict[str, list[str]] = defaultdict(list)
    speaker_duration: dict[str, float] = defaultdict(float)
    speaker_turns: dict[str, int] = defaultdict(int)

    for seg in segments:
        spk = seg.get("speaker", "UNKNOWN")
        text = seg.get("text", "")
        dur = seg.get("end", 0) - seg.get("start", 0)
        speaker_turns[spk] += 1
        speaker_duration[spk] += dur
        if text and len(speaker_phrases[spk]) < max_phrases:
            speaker_phrases[spk].append(text[:phrase_len])

    unique_speakers = sorted(speaker_phrases.keys())
    total_dur = sum(speaker_duration.values())
    total = len(unique_speakers)

    print(f"\n[speaker_labeler] {total} speaker(s) detected.\n")

    # ── Stats overview ──
    for spk in unique_speakers:
        pct = speaker_duration[spk] / total_dur * 100 if total_dur else 0
        print(f"  {spk}: {speaker_turns[spk]} turns | {speaker_duration[spk]:.0f}s ({pct:.1f}%)")

    print()

    # ── Verification step ──
    if expected_speakers and total != expected_speakers:
        print(f"⚠️  Expected {expected_speakers} speaker(s) but detected {total}.")
        print("   Consider re-running diarize() with num_speakers set explicitly.\n")

    confirm = input(f"Does {total} speaker(s) look correct? (Enter=yes / type correct number to retry hint): ").strip()
    if confirm.isdigit():
        print(f"[speaker_labeler] Note: re-run diarize(audio, num_speakers={confirm}) to get better separation.\n")

    # ── Per-speaker sample phrases ──
    print("\n─── Sample phrases per speaker ───\n")
    for _i, spk in enumerate(unique_speakers, 1):
        print(f"[{spk}] ({speaker_turns[spk]} turns, {speaker_duration[spk]:.0f}s)")
        for j, p in enumerate(speaker_phrases[spk], 1):
            print(f"  {j}. {p}")
        print()

    # ── Labeling ──
    mapping = {}
    print("─── Identify each speaker ───\n")
    for spk in unique_speakers:
        name = input(f"Name for {spk} (Enter to keep as {spk}): ").strip()
        mapping[spk] = name if name else spk

    return mapping


def apply_labels(segments: list[dict], mapping: dict[str, str]) -> list[dict]:
    """Apply name mapping to segments."""
    labeled = []
    for seg in segments:
        new_seg = dict(seg)
        anon = seg.get("speaker", "UNKNOWN")
        new_seg["speaker"] = mapping.get(anon, anon)
        labeled.append(new_seg)
    return labeled
