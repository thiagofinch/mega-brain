"""
Voice Diarizer — Segment audio by speaker using pyannote.audio (local)
or AssemblyAI (cloud fallback).
"""
from pathlib import Path
from typing import List, Dict, Optional


def diarize_local(audio_file: str, num_speakers: Optional[int] = None) -> List[Dict]:
    """
    Diarize using pyannote.audio.
    Returns list of {speaker, start, end} dicts.
    """
    try:
        from pyannote.audio import Pipeline
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=False
        )
        params = {}
        if num_speakers:
            params["num_speakers"] = num_speakers
        diarization = pipeline(audio_file, **params)
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "speaker": speaker,
                "start": turn.start,
                "end": turn.end
            })
        return segments
    except ImportError:
        return []
    except Exception as e:
        print(f"[voice_diarizer] pyannote error: {e}")
        return []


def diarize_assemblyai(audio_file: str) -> List[Dict]:
    """
    Diarize using AssemblyAI cloud (fallback).
    Returns list of {speaker, start, end, text} dicts.
    """
    try:
        import assemblyai as aai
        import os
        aai.settings.api_key = os.environ.get("ASSEMBLYAI_API_KEY", "")
        if not aai.settings.api_key:
            return []
        config = aai.TranscriptionConfig(speaker_labels=True)
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_file, config=config)
        segments = []
        for utt in transcript.utterances or []:
            segments.append({
                "speaker": f"SPEAKER_{utt.speaker}",
                "start": utt.start / 1000.0,
                "end": utt.end / 1000.0,
                "text": utt.text
            })
        return segments
    except ImportError:
        return []
    except Exception as e:
        print(f"[voice_diarizer] AssemblyAI error: {e}")
        return []


def diarize(audio_file: str, num_speakers: Optional[int] = None) -> List[Dict]:
    """
    Diarize with local-first, cloud fallback strategy.
    """
    segments = diarize_local(audio_file, num_speakers)
    if not segments:
        print("[voice_diarizer] Local diarization failed, trying AssemblyAI...")
        segments = diarize_assemblyai(audio_file)
    return segments
