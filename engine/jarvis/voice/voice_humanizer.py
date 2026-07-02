# voice_humanizer.py
"""
JARVIS Voice Humanizer
======================
Adiciona Audio Tags do ElevenLabs v3 para tornar a voz mais natural e expressiva.

Funcionalidades:
- Detecta emoções no texto e adiciona tags apropriadas
- Adiciona pausas naturais, suspiros, risos secos
- Transforma texto robótico em fala humanizada

Reference: https://elevenlabs.io/blog/v3-audiotags
"""

import re


class VoiceHumanizer:
    """
    Transforma texto em fala humanizada usando Audio Tags do ElevenLabs v3.
    """

    # ==============================
    # PADRÕES DE DETECÇÃO DE EMOÇÃO
    # ==============================

    EMOTION_PATTERNS = {
        # Sarcasmo / Ironia (JARVIS é mestre nisso)
        "sarcasm": [
            r"fascinante",
            r"interessante(?:\.\.\.|…)",
            r"claro que",
            r"obviamente",
            r"claramente",
            r"como sempre",
            r"não me diga",
            r"que surpresa",
            r"senhor sabe melhor",
            r"de nada",
        ],
        # Preocupação sutil
        "concern": [
            r"são \d+ da manhã",
            r"está cansado",
            r"dormiu",
            r"deveria descansar",
            r"sua saúde",
            r"preocupante",
        ],
        # Satisfação / Orgulho
        "satisfaction": [
            r"bom trabalho",
            r"excelente",
            r"impressionado",
            r"muito bom",
            r"ficou.*bom",
            r"funcionando",
            r"completo",
            r"pronto",
        ],
        # Pensando / Processando
        "thinking": [
            r"hmm",
            r"interessante",
            r"deixe-me ver",
            r"analisando",
            r"verificando",
            r"processando",
            r"momento",
        ],
        # Frustração leve
        "frustration": [
            r"de novo",
            r"já discutimos",
            r"três vezes",
            r"avisei",
            r"problema",
            r"erro",
        ],
        # Formalidade / Respeito
        "formal": [
            r"senhor",
            r"às suas ordens",
            r"permita-me",
            r"se me permite",
        ],
    }

    # ==============================
    # MAPEAMENTO DE EMOÇÃO PARA AUDIO TAGS
    # ==============================

    EMOTION_TAGS = {
        "sarcasm": "[dry tone]",
        "concern": "[softly]",
        "satisfaction": "[warmly]",
        "thinking": "[thoughtfully]",
        "frustration": "[sighs]",
        "formal": "[composed]",
    }

    # ==============================
    # PADRÕES DE SUBSTITUIÇÃO PARA NATURALIDADE
    # ==============================

    NATURALNESS_PATTERNS = [
        # Adicionar pausas dramáticas após pontos importantes
        (r"\.{3}|…", "... [pause]"),
        # Risada seca após comentários sarcásticos
        (r"(Não se acostume\.)", r"\1 [soft chuckle]"),
        (r"(De nada\.)", r"[sighs] \1"),
        # Suspiros antes de explicações longas
        (r"(Bem,|Então,|Veja bem,)", r"[sighs] \1"),
        # Tom pensativo para perguntas retóricas
        (r"(\?.*\?)", r"[thoughtfully] \1"),
    ]

    # ==============================
    # FRASES DO JARVIS COM TAGS ESPECÍFICAS
    # ==============================

    # Frases que recebem tags NO INÍCIO (não substituição inline)
    # Formato: pattern -> tag a adicionar no início da frase
    SENTENCE_STARTERS = {
        r"^Às suas ordens": "[composed]",
        r"decidiu aparecer": "[dry tone]",
        r"^Phase \d": "[professionally]",
        r"^\d+ insights": "[professionally]",
        r"^Fascinante": "[dry tone]",
        r"^Interessante": "[thoughtfully]",
        r"^Devo admitir": "[warmly]",
        r"^Hmm": "[thoughtfully]",
        r"são \d+ da (manhã|madrugada)": "[softly]",
        r"^Posso executar": "[dry tone]",
        r"^Muito bom": "[warmly]",
        r"^Excelente": "[warmly]",
    }

    # Substituições inline específicas
    INLINE_REPLACEMENTS = {
        "como sempre.": "[sighs] como sempre.",
        "Não se acostume.": "Não se acostume. [soft chuckle]",
        "De nada.": "[sighs] De nada.",
        "...": "... [pause]",
    }

    def __init__(self):
        """Inicializa o humanizer."""
        # Compilar patterns para performance
        self.compiled_patterns = {}
        for emotion, patterns in self.EMOTION_PATTERNS.items():
            self.compiled_patterns[emotion] = [re.compile(p, re.IGNORECASE) for p in patterns]

    def detect_emotion(self, text: str) -> str:
        """
        Detecta a emoção predominante no texto.

        Returns:
            Nome da emoção ou "neutral"
        """
        scores = {}

        for emotion, patterns in self.compiled_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern.search(text):
                    score += 1
            if score > 0:
                scores[emotion] = score

        if scores:
            return max(scores, key=scores.get)
        return "neutral"

    def add_emotion_tags(self, text: str) -> str:
        """
        Adiciona tags de emoção baseado no conteúdo.
        """
        emotion = self.detect_emotion(text)

        if emotion != "neutral":
            tag = self.EMOTION_TAGS.get(emotion, "")
            if tag and not text.startswith("["):
                text = f"{tag} {text}"

        return text

    def apply_jarvis_phrases(self, text: str) -> str:
        """
        Aplica tags específicas para frases conhecidas do JARVIS.
        Processa frase por frase para evitar duplicações.
        """
        # Primeiro, aplicar substituições inline simples
        for phrase, replacement in self.INLINE_REPLACEMENTS.items():
            text = text.replace(phrase, replacement)

        # Depois, processar frases para adicionar tags no início
        sentences = re.split(r"(?<=[.!?])\s+", text)
        result = []

        for sentence in sentences:
            tagged = False
            for pattern, tag in self.SENTENCE_STARTERS.items():
                if re.search(pattern, sentence, re.IGNORECASE):
                    # Só adiciona tag se a frase ainda não tem tag
                    if not sentence.strip().startswith("["):
                        sentence = f"{tag} {sentence}"
                    tagged = True
                    break
            result.append(sentence)

        return " ".join(result)

    def add_naturalness(self, text: str) -> str:
        """
        Adiciona elementos de naturalidade (pausas, suspiros, etc).
        """
        for pattern, replacement in self.NATURALNESS_PATTERNS:
            text = re.sub(pattern, replacement, text)
        return text

    def add_breathing_pauses(self, text: str) -> str:
        """
        Adiciona pausas de respiração em frases longas.
        Frases com mais de 50 caracteres ganham uma pausa natural.
        """
        sentences = text.split(". ")
        result = []

        for i, sentence in enumerate(sentences):
            if len(sentence) > 80 and "[pause]" not in sentence:
                # Encontrar vírgula central para adicionar pausa
                mid = len(sentence) // 2
                comma_pos = sentence.find(",", mid - 20, mid + 20)
                if comma_pos > 0:
                    sentence = sentence[: comma_pos + 1] + " [breath]" + sentence[comma_pos + 1 :]
            result.append(sentence)

        return ". ".join(result)

    def humanize(self, text: str) -> str:
        """
        Aplica todas as transformações para humanizar o texto.

        Args:
            text: Texto original

        Returns:
            Texto com Audio Tags para voz mais natural
        """
        # 1. Aplicar frases específicas do JARVIS (tags localizadas)
        text = self.apply_jarvis_phrases(text)

        # 2. Se não começou com tag, adicionar emoção geral
        if not text.strip().startswith("["):
            text = self.add_emotion_tags(text)

        # 3. Adicionar pausas de respiração em frases longas
        text = self.add_breathing_pauses(text)

        # 4. Limpar tags duplicadas ou conflitantes
        text = self._clean_tags(text)

        return text

    def _clean_tags(self, text: str) -> str:
        """Remove tags duplicadas ou adjacentes."""
        # Remover tags duplicadas adjacentes
        text = re.sub(r"\[(\w+)\]\s*\[\1\]", r"[\1]", text)

        # Remover espaços extras
        text = re.sub(r"\s+", " ", text)

        # Garantir espaço após tags
        text = re.sub(r"\]([a-zA-Z])", r"] \1", text)

        return text.strip()


# ==============================
# FACTORY
# ==============================

_humanizer = None


def get_humanizer() -> VoiceHumanizer:
    """Retorna instância singleton do humanizer."""
    global _humanizer
    if _humanizer is None:
        _humanizer = VoiceHumanizer()
    return _humanizer


def humanize_text(text: str) -> str:
    """Conveniência para humanizar texto."""
    return get_humanizer().humanize(text)


# ==============================
# TESTE
# ==============================

if __name__ == "__main__":
    humanizer = VoiceHumanizer()

    test_cases = [
        "Às suas ordens, senhor.",
        "Ah, o senhor decidiu aparecer. O sistema sentiu sua falta. Eu apenas continuei trabalhando, como sempre.",
        "Fascinante. E a informação que precisamos está exatamente nesse arquivo.",
        "Devo admitir, não esperava essa solução. Estou... impressionado. Não se acostume.",
        "São 4 da manhã. Seu raciocínio estava 40% melhor há seis horas.",
        "Phase 4 completa. 1.847 insights. 312 heurísticas. Zero atalhos.",
        "O senhor está ciente de que já discutimos isso três vezes?",
        "Hmm. Isso é mais interessante do que parece à primeira vista...",
    ]

    print("=" * 70)
    print("VOICE HUMANIZER - TESTE")
    print("=" * 70)

    for text in test_cases:
        print("\n📝 Original:")
        print(f"   {text}")
        print("\n🎤 Humanizado:")
        print(f"   {humanizer.humanize(text)}")
        print("-" * 70)
