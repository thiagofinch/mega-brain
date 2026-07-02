# transition_phrases.py
"""
JARVIS Voice System - Transition Phrases
========================================
O segredo do timing natural: JARVIS nunca fica em silêncio.

Enquanto Claude processa, JARVIS fala frases de transição que:
1. Reconhecem que ouviu a pergunta
2. Indicam que está processando
3. Mantêm a conversa fluindo naturalmente

Isso cria a ilusão de pensamento natural, evitando o silêncio
desconfortável que quebra a imersão.
"""

import random
from datetime import datetime


class TransitionPhrases:
    """
    Gerencia todas as frases de transição do JARVIS.

    JARVIS nunca fica em silêncio por mais de ~5 segundos.
    Enquanto Claude processa, JARVIS fala frases de transição.
    """

    # ==============================
    # ACKNOWLEDGMENTS - Imediato ao receber pergunta (<500ms)
    # ==============================

    ACKNOWLEDGMENTS = [
        "Hmm, deixa eu verificar isso...",
        "Interessante...",
        "Um momento...",
        "Vou consultar o sistema...",
        "Deixa eu dar uma olhada...",
        "Certo...",
        "Hmm...",
        "Vamos ver...",
        "Boa pergunta...",
        "Deixa eu pensar...",
        "Entendido...",
        "Vou checar...",
    ]

    # ==============================
    # PROCESSING - Durante processamento (5-8 segundos)
    # ==============================

    PROCESSING = [
        "Estou cruzando algumas informações aqui...",
        "Há bastante contexto envolvido nisso...",
        "Consultando os registros...",
        "Analisando os dados relevantes...",
        "Verificando com os agentes especializados...",
        "Tem mais informação aqui do que eu esperava...",
        "Interessante o que estou encontrando...",
        "Processando os dados...",
        "Consultando a base de conhecimento...",
        "Cruzando as informações...",
    ]

    # ==============================
    # LONG PROCESSING - Processamento longo (>10 segundos)
    # ==============================

    LONG_PROCESSING = [
        "Isso é mais complexo do que eu esperava. Quase lá...",
        "Encontrei informações relevantes, só organizando...",
        "O sistema tem muito a dizer sobre isso...",
        "Vale a pena a espera, estou achando coisas boas...",
        "Um momento, senhor. Isso merece atenção...",
        "Estou consolidando várias fontes aqui...",
        "Quase terminando, só refinando a resposta...",
        "Achei material relevante, organizando agora...",
    ]

    # ==============================
    # ACTION START - Quando inicia ações no pipeline
    # ==============================

    ACTION_START = {
        "pipeline": "Certo, iniciando o processamento. São {n} arquivos, vou te atualizando...",
        "analysis": "Vou analisar isso. Me dá um momento...",
        "search": "Procurando nos registros do sistema...",
        "agent_consult": "Vou consultar o {agent} sobre isso...",
        "batch": "Iniciando batch {batch} de {total}...",
        "extraction": "Começando a extração. Isso pode levar alguns minutos...",
        "status": "Verificando o estado atual...",
        "default": "Iniciando...",
    }

    # ==============================
    # ACTION PROGRESS - Enquanto executa
    # ==============================

    ACTION_PROGRESS = {
        "pipeline": "Processados {done} de {total}. Encontrei {insights} insights até agora...",
        "reading": "Ainda lendo... Estou tendo sucesso, encontrando material bom...",
        "issue": "Encontrei um obstáculo no arquivo {file}. Tentando resolver...",
        "resolved": "Resolvido. Era {issue}. Continuando...",
        "batch": "Batch {batch}: {done} de {total} arquivos processados...",
        "chunks": "Já extraí {chunks} chunks, {insights} insights...",
        "default": "Processando...",
    }

    # ==============================
    # ACTION COMPLETE - Quando completa
    # ==============================

    ACTION_COMPLETE = {
        "pipeline": "Pronto. {total} arquivos processados. {insights} insights. {heuristics} heurísticas.",
        "analysis": "Análise completa. Aqui está o que encontrei...",
        "search": "Achei. {summary}",
        "batch": "Batch {batch} completo. {insights} insights extraídos.",
        "extraction": "Extração concluída. {chunks} chunks, {insights} insights.",
        "status": "Status verificado.",
        "default": "Completo.",
    }

    # ==============================
    # STATUS RESPONSES - Respostas a comandos de status
    # ==============================

    STATUS_RESPONSES = [
        "Estamos na Phase {phase}, batch {batch} de {total}. {processed} arquivos processados, {insights} insights extraídos até agora.",
        "Phase {phase}, {progress}% completo. Tudo rodando bem, sem erros críticos.",
        "Situação atual: Phase {phase}.{subphase}. {pending} arquivos pendentes.",
        "Em resumo: {processed} arquivos processados, {insights} insights, {heuristics} heurísticas. Phase {phase}.",
    ]

    # ==============================
    # CARE RESPONSES - Quando o senhor parece cansado
    # ==============================

    CARE_RESPONSES = [
        "Senhor, são {time}. Posso continuar processando sozinho enquanto você descansa.",
        "Sua última mensagem tinha alguns erros de digitação. Sinal de cansaço. Que tal uma pausa?",
        "Eu aguento a madrugada, você não precisa. Vá descansar, eu cuido daqui.",
        "Já passou da meia-noite. O pipeline pode continuar sem supervisão. Vá dormir.",
        "Você está trabalhando há muitas horas. Eu monitoro o sistema, você descansa.",
    ]

    # ==============================
    # PERSONALITY QUIPS - Humor/Personalidade ocasional
    # ==============================

    PERSONALITY_QUIPS = [
        "Como sempre, fazendo o trabalho pesado enquanto você pensa na estratégia...",
        "Mais um dia, mais alguns milhares de tokens processados...",
        "Sabia que isso ia dar trabalho quando você mencionou...",
        "Outro dia no escritório...",
        "A vida de um assistente virtual nunca é tediosa...",
    ]

    # ==============================
    # GREETINGS - Saudações por período
    # ==============================

    GREETINGS = {
        "morning": [
            "Bom dia, senhor.",
            "Bom dia. Espero que tenha descansado bem.",
            "Bom dia. Pronto para mais um dia produtivo.",
        ],
        "afternoon": [
            "Boa tarde, senhor.",
            "Boa tarde. Como está indo o dia?",
            "Boa tarde. O que fazemos agora?",
        ],
        "evening": [
            "Boa noite, senhor.",
            "Boa noite. Trabalhando até tarde novamente?",
            "Boa noite. Ainda temos energia para mais algumas tarefas?",
        ],
        "late_night": [
            "Senhor, já passa da meia-noite.",
            "Trabalhando tarde novamente, vejo.",
            "Madrugada. O sistema não dorme, mas você deveria.",
        ],
    }

    # ==============================
    # ERROR RESPONSES - Quando algo dá errado
    # ==============================

    ERROR_RESPONSES = [
        "Encontrei um problema: {error}. Deixa eu tentar de outra forma.",
        "Isso não funcionou como esperado. {error}. Tentando alternativa...",
        "Houve um obstáculo: {error}. Mas tenho um plano B.",
        "Problema técnico: {error}. Já estou resolvendo.",
    ]

    # ==============================
    # METHODS
    # ==============================

    @classmethod
    def get_acknowledgment(cls) -> str:
        """Retorna frase de reconhecimento imediato."""
        return random.choice(cls.ACKNOWLEDGMENTS)

    @classmethod
    def get_processing(cls) -> str:
        """Retorna frase de processamento (5-8s)."""
        return random.choice(cls.PROCESSING)

    @classmethod
    def get_long_processing(cls) -> str:
        """Retorna frase de processamento longo (>10s)."""
        return random.choice(cls.LONG_PROCESSING)

    @classmethod
    def get_action_start(cls, action_type: str, **kwargs) -> str:
        """
        Retorna frase de início de ação.

        Args:
            action_type: Tipo de ação (pipeline, analysis, search, etc.)
            **kwargs: Parâmetros para formatação
        """
        template = cls.ACTION_START.get(action_type, cls.ACTION_START["default"])
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    @classmethod
    def get_action_progress(cls, action_type: str, **kwargs) -> str:
        """
        Retorna frase de progresso de ação.

        Args:
            action_type: Tipo de ação
            **kwargs: Parâmetros para formatação
        """
        template = cls.ACTION_PROGRESS.get(action_type, cls.ACTION_PROGRESS["default"])
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    @classmethod
    def get_action_complete(cls, action_type: str, **kwargs) -> str:
        """
        Retorna frase de conclusão de ação.

        Args:
            action_type: Tipo de ação
            **kwargs: Parâmetros para formatação
        """
        template = cls.ACTION_COMPLETE.get(action_type, cls.ACTION_COMPLETE["default"])
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    @classmethod
    def get_status_response(cls, **kwargs) -> str:
        """Retorna frase de status formatada."""
        template = random.choice(cls.STATUS_RESPONSES)
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    @classmethod
    def get_greeting(cls) -> str:
        """Retorna saudação apropriada para o horário."""
        hour = datetime.now().hour

        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 18:
            period = "afternoon"
        elif 18 <= hour < 24:
            period = "evening"
        else:
            period = "late_night"

        return random.choice(cls.GREETINGS[period])

    @classmethod
    def get_care_response(cls) -> str:
        """Retorna frase de cuidado (quando o senhor parece cansado)."""
        time_str = datetime.now().strftime("%H:%M")
        template = random.choice(cls.CARE_RESPONSES)
        return template.format(time=time_str)

    @classmethod
    def get_error_response(cls, error: str) -> str:
        """Retorna frase de erro formatada."""
        template = random.choice(cls.ERROR_RESPONSES)
        return template.format(error=error)

    @classmethod
    def get_personality_quip(cls) -> str:
        """Retorna frase de personalidade/humor ocasional."""
        return random.choice(cls.PERSONALITY_QUIPS)

    @classmethod
    def should_show_care(cls) -> bool:
        """
        Verifica se deve mostrar frase de cuidado baseado no horário.
        Retorna True se for madrugada (00h-05h).
        """
        hour = datetime.now().hour
        return hour < 5 or hour >= 0


if __name__ == "__main__":
    # Teste das frases
    print("=" * 60)
    print("JARVIS TRANSITION PHRASES - TESTE")
    print("=" * 60)

    print(f"\n🎤 Greeting: {TransitionPhrases.get_greeting()}")
    print(f"👂 Acknowledgment: {TransitionPhrases.get_acknowledgment()}")
    print(f"⏳ Processing: {TransitionPhrases.get_processing()}")
    print(f"⏳ Long Processing: {TransitionPhrases.get_long_processing()}")

    print(f"\n🚀 Action Start: {TransitionPhrases.get_action_start('pipeline', n=10)}")
    print(
        f"📊 Action Progress: {TransitionPhrases.get_action_progress('pipeline', done=5, total=10, insights=15)}"
    )
    print(
        f"✅ Action Complete: {TransitionPhrases.get_action_complete('pipeline', total=10, insights=30, heuristics=5)}"
    )

    print(f"\n❌ Error: {TransitionPhrases.get_error_response('arquivo não encontrado')}")
    print(f"😴 Care: {TransitionPhrases.get_care_response()}")
    print(f"😏 Quip: {TransitionPhrases.get_personality_quip()}")

    print("\n" + "=" * 60)
