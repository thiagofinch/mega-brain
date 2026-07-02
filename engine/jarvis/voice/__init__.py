# JARVIS Voice System
# ===================
# Sistema de assistente de voz integrado ao Mega Brain

__version__ = "1.0.0"
__author__ = "[OWNER]"

from .config import Config
from .mega_brain_connector import MegaBrainConnector
from .orchestrator import JarvisOrchestrator
from .stt_handler import STTHandler, create_stt_handler
from .transition_phrases import TransitionPhrases
from .tts_handler import TTSHandler, create_tts_handler

__all__ = [
    "Config",
    "JarvisOrchestrator",
    "MegaBrainConnector",
    "STTHandler",
    "TTSHandler",
    "TransitionPhrases",
    "create_stt_handler",
    "create_tts_handler",
]
