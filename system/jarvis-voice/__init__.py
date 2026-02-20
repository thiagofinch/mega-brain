# JARVIS Voice System
# ===================
# Sistema de assistente de voz integrado ao Mega Brain

__version__ = "1.0.0"
__author__ = "[OWNER]"

from .config import Config
from .orchestrator import JarvisOrchestrator
from .tts_handler import TTSHandler, create_tts_handler
from .stt_handler import STTHandler, create_stt_handler
from .mega_brain_connector import MegaBrainConnector
from .transition_phrases import TransitionPhrases

__all__ = [
    "Config",
    "JarvisOrchestrator",
    "TTSHandler",
    "STTHandler",
    "MegaBrainConnector",
    "TransitionPhrases",
    "create_tts_handler",
    "create_stt_handler",
]
