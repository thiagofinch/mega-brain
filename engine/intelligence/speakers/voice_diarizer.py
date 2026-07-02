"""
Voice Diarizer — Segment audio by speaker using pyannote.audio (local)
or AssemblyAI (cloud fallback).
"""


def diarize_local(audio_file: str, num_speakers: int | None = None) -> list[dict]:
    """
    Diarize using pyannote.audio.
    Returns list of {speaker, start, end} dicts.
    """
    try:
        from pyannote.audio import Pipeline

        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", use_auth_token=False
        )
        params = {}
        if num_speakers:
            params["num_speakers"] = num_speakers
        diarization = pipeline(audio_file, **params)
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({"speaker": speaker, "start": turn.start, "end": turn.end})
        return segments
    except ImportError:
        return []
    except Exception as e:
        print(f"[voice_diarizer] pyannote error: {e}")
        return []


def diarize_assemblyai(
    audio_file: str, num_speakers: int | None = None, language_code: str = "pt"
) -> list[dict]:
    """
    Diarize using AssemblyAI cloud (fallback).
    Returns list of {speaker, start, end, text} dicts.
    num_speakers: hint to API — avoids collapsing multiple speakers into fewer groups.
    """
    try:
        import os

        import assemblyai as aai

        aai.settings.api_key = os.environ.get("ASSEMBLYAI_API_KEY", "")
        if not aai.settings.api_key:
            return []
        config = aai.TranscriptionConfig(
            speaker_labels=True,
            language_code=language_code,
            speakers_expected=num_speakers,  # None = auto-detect (may under-count)
        )
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_file, config=config)
        if transcript.status == aai.TranscriptStatus.error:
            print(f"[voice_diarizer] AssemblyAI error: {transcript.error}")
            return []
        segments = []
        for utt in transcript.utterances or []:
            segments.append(
                {
                    "speaker": f"SPEAKER_{utt.speaker}",
                    "start": utt.start / 1000.0,
                    "end": utt.end / 1000.0,
                    "text": utt.text,
                }
            )
        detected = len({s["speaker"] for s in segments})
        print(
            f"[voice_diarizer] AssemblyAI: {detected} speaker(s) detected"
            + (f" (hint: {num_speakers})" if num_speakers else " (auto-detect)")
        )
        return segments
    except ImportError:
        return []
    except Exception as e:
        print(f"[voice_diarizer] AssemblyAI error: {e}")
        return []


def diarize(
    audio_file: str, num_speakers: int | None = None, language_code: str = "pt"
) -> list[dict]:
    """
    Diarize with local-first, cloud fallback strategy.
    Pass num_speakers if you know how many people are in the recording —
    without it the API may merge distinct voices into fewer groups.
    """
    segments = diarize_local(audio_file, num_speakers)
    if not segments:
        print("[voice_diarizer] Local diarization failed, trying AssemblyAI...")
        segments = diarize_assemblyai(
            audio_file, num_speakers=num_speakers, language_code=language_code
        )
    return segments
