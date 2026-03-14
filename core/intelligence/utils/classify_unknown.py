#!/usr/bin/env python3
"""
Script para classificar e mover arquivos de _UNKNOWN para pastas corretas.
"""

import os
import re
import shutil
import sys
from pathlib import Path

# Configurar encoding para UTF-8 no Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Diretórios
INBOX_BASE = Path(r"c:\Users\thiag\OneDrive\Documentos\Mega Brain\00-INBOX")
UNKNOWN_DIR = INBOX_BASE / "_UNKNOWN"

# Pastas de destino
DESTINATIONS = {
    "ALEX_HORMOZI": INBOX_BASE / "ALEX HORMOZI (ACQUISITION.COM)",
    "JEREMY_HAYNES": INBOX_BASE / "JEREMY HAYNES",
    "G4_EDUCACAO": INBOX_BASE / "G4 EDUCACAO (GESTAO 4.0)",
    "FULL_SALES_SYSTEM": INBOX_BASE / "FULL SALES SYSTEM",
    "COLE_GORDON": INBOX_BASE / "COLE GORDON (CLOSERS.IO)",
    "SAM_OVEN": INBOX_BASE / "SAM OVEN (SETTERLUN UNIVERSITY)",
}

# Patterns de classificação
PATTERNS = {
    # Alex Hormozi: conteúdo em inglês, frases características
    "ALEX_HORMOZI": [
        r"HOW TO SELL BETTER THAN",
        r"FEELS ILLEGAL",
        r"HOW I SCALED.*SALES",
        r"ACQUISITION",
        r"GYM LAUNCH",
        r"\d+ HOUR ULTIMATE GUIDE",
        r"SALES WAS HARD UNTIL",
        r"CONCEPTS.*SALES",
        r"HORMOZI",
        r"100M",
        r"\$100M",
        r"GROW YOUR BUSINESS.*FAST",
        r"GET CUSTOMERS.*FAST",
        r"HOW I BUILT.*SALES TEAM",
        r"BUILD LARGE SALES TEAMS",
        r"HOW I RAISE PRICES",
        r"MY BEST SALES TACTIC",
        r"GET YOUR FIRST.*CUSTOMERS",
        r"SELL ANYTHING TO ANYONE",
        r"INCREASE AVERAGE ORDER VALUE",
        r"CREATE REAL SCARCITY",
        r"MAKE A TON OF MONEY",
        r"UNUSUAL METHOD",
        r"PSYCHOLOGICAL TRICK",
        r"STARTING FROM 0",
        r"EMPLOYEE BRAIN SYNDROME",
        r"WEIGHT LOSS",
        r"LEAD GENERATION STRATEGY",
        r"SECRET TO.*SALES SUCCESS",
    ],
    # Jeremy Haynes: inglês com datas no formato MM-DD-YY
    "JEREMY_HAYNES": [
        r"\d{1,2}-\d{1,2}-\d{2,4}\.txt$",  # Data no final: 3-2-24, 12-16-23
        r"BEST PRACTICES",
        r"CALL FUNNELS?",
        r"AUDIENCE TARGETING",
        r"AD OPTIMIZATION",
        r"CREATIVE TESTING",
        r"FUNNEL ADS",
        r"RICH PEOPLE MESSAGING",
        r"PREPPING FOR Q4",
        r"ORGANIC CONTENT ENGINE",
        r"UNIQUE MECHANISM",
        r"LINKEDIN STRATEGIES",
        r"LONGTERM VISION",
        r"ENTREPRENEUR SELF CARE",
        r"HOW TO ONBOARD A CLIENT",
        r"MONTHLY ACTIONS TO STAY AHEAD",
        # Colaboradores Jeremy Haynes (Megalodon Marketing)
        r"BRANDON CARTER",
        r"BOLDCEO",
        r"NICK THERIOT",
        r"AMBER MORNINGSTAR",
        r"BREZSCALES",
        r"MINI WEBINAR",
        r"LAUNCH PLAN",
        r"MEGALODON",
        r"OFFER MESSAGING",
        r"VSL STRUCTURE",
        r"MEDIA BUYING",
        r"IDEAL CLIENT AVATAR",
        r"SCALING CHECKLIST",
        r"OBJECTION CRUSHER",
        r"MARKETING TIPS",
    ],
    # G4 Educação: formato M1 A1, M2 A2, etc.
    "G4_EDUCACAO": [
        r"M\d+ A\d+",  # M1 A1, M2 A2, etc.
        r"M\d+_A\d+",  # M1_A1 format
        r"FCX",  # Livro FCX
        r"G4.*ACELERA",  # Livro G4 Aceleração
        r"DESAFIOS DO MERCADO",
        r"TIPOS DE LEADS",
        r"TRAZER OS LEADS CORRETOS",
        r"MODELOS DE QUALIFICA",
        r"SALES KANBAN",
        r"CULTURA DE ALTA PERFORMANCE",
        r"ATRIBUI.*SDR.*INBOUND",
        r"PLANEJAMENTO.*CRM",
        r"PRINCIPAIS ERROS.*SDR",
        r"CURR.*CULO.*EXPERI",
        r"PROCESSO SELETIVO EM VENDAS",
        r"PRIMEIRO EMPREGO EM VENDAS",
        r"CRIT.*RIOS.*DEFINIR ICP",
        r"INBOUND SALES.*OUTBOUND",
    ],
    # Full Sales System: CURSO 7/16/21, MOD X AULA Y, CLOSER AGUIA, DIA X
    "FULL_SALES_SYSTEM": [
        r"CURSO \d+",  # CURSO 7, CURSO 16, CURSO 21
        r"MOD \d+ AULA \d+",  # MOD 1 AULA 2
        r"MOD \d+ A\d+",  # Alternative format
        r"DIA \d+.*MANH[ÃA]",  # DIA 03 - MANHÃ
        r"DIA \d+.*TARDE",  # DIA 03 - TARDE
        r"CLOSER AGUIA",
        r"Á\.G\.U\.I\.A",
        r"VENDA DE IMPACTO",
        r"CLOSER ÁGUIA",
        r"VENDAS 1X1",
        r"GATILHOS MENTAIS",
        r"SPIN SELLING.*HOTSEAT",
        r"DOWNSELL",
        r"TÉCNICAS DE FECHAMENTO",
        r"ARMAS DE FECHAMENTO",
        r"ESTRUTURA DA VENDA",
        r"CONSTRUÇÃO DE VENDA",
        r"PACTO (INICIAL|FINAL)",
        r"QUADRO DE ESTRATÉGIAS",
        r"LIMITES E MARGEM",
        r"NEGOCIAÇÃO (DE )?CICLO",
        r"PERFORMANCE PARA VENDER",
        r"PRÉ-PITCH",
        r"ESTRUTURA DE PITCH",
        r"TÉCNICAS DE URGÊNCIA",
        r"WARM-UP E EMOÇÃO",
        r"PRINCÍPIOS DE FECHAMENTO",
        r"OBJEÇÕES",
        r"CAINDO O PRODUTO",
        r"PEGANDO O PAGAMENTO",
        r"INTRODUÇÃO.*QUEBRA GELO",
        r"RITUAL DE PRÉ-ATENDIMENTO",
        r"NEGOCIAÇÃO COMERCIAL",
    ],
    # Cole Gordon: inglês sem datas, foco em sales/closing
    "COLE_GORDON": [
        r"VALUE ADDED.*QUESTIONS",
        r"SELFISH QUESTIONS",
        r"WHEN TO FIRE SALES",
        r"GOAT CLOSING",
        r"HOW CAN YOU GUARANTEE",
        r"FIT TEA CEO",
        r"SALES TRAINING FOR 2025",
        r"USING LOANS WISELY",
        r"PROMPTS PARA CRIAÇÃO DE SCRIPTS",
        # Colaboradores Cole Gordon (Closers.io)
        r"JOSH TROY",
        r"RYAN CLOG",
        r"HYDRA SALES",
        r"SALES Q\s*&?\s*A",
        r"MASTERCLASS DE ESTRUTURA",
        r"CALL FUNNEL MASTERY",
        r"HOW TO RECRUIT.*SALES",
        r"TOOLS.*SOFTWARE.*CLOSERS",
        r"POST SALES CALL",
        r"MAXIMIZING SETTER",
        r"CLOSER PERFORMANCE",
        r"APPLICATION FUNNEL",
        r"HOW TO MANAGE CLOSERS",
        r"KEEP YOUR MORAL",
        r"TRAIN.*MAINTAIN.*SALES TEAM",
        r"FULL TIME CLOSERS",
        r"HOW TO STEP IN.*MOTIVATE",
        r"NEW METHOD TO CLOSE",
        r"AFTER CLOSING.*SALES",
        # Objection handling patterns (Cole Gordon specialty)
        r"OBJECTION",
        r"I CANT AFFORD",
        r"I NEED TO THINK",
        r"RATHER GET STARTED NEXT",
        r"FOLLOW.?UP SYSTEM",
        r"GHOSTED LEADS",
        r"CONVERTS.*LEADS",
        r"KILLER FOLLOW",
        # Numbered sales training files
        r"^\d+\.\s+(?:OBJECTION|HOW TO|WHAT TO)",
        # More objection patterns (numbered format)
        r"^\d+[\.\s]+(?:IM TRAVELING|I DIDNT EXPECT|WHAT HAPPENS IF)",
        r"^\d+[\.\s]+(?:CAN I SPEAK|MY BUSINESS PARTNER|I HAVE TO GET MY LAWYER)",
        r"^\d+[\.\s]+(?:I SAW A NEGATIVE|ARE YOU OPEN TO|I AM LOOKING AT)",
        r"^\d+[\.\s]+(?:HOW DO I KNOW|WHY ARE YOU BETTER)",
        # Sales training numbered files
        r"^\d+[\.\s]*(?:REVIEWING CALLS|USING SALES VIDEOS|RAISING THE CLIENT)",
        r"^\d+[\.\s]*(?:GET LEADS BACK|WHY YOU SHOULD TEXT|YOUR PERSONAL LIFE)",
        r"^\d+[\.\s]*ATTACKING BUSINESS BOTTLENECKS",
        # Collaborators (Zach patterns)
        r"W ZACH",
    ],
    # Sam Oven / Setterlun: workshop, consulting niche
    "SAM_OVEN": [
        r"9 FIGURE WORKSHOP",
        r"CLIENT ACCELERATORS",
        r"CONSULTING NICHE",
        r"HIGH TICKET OFFER",
        r"FREEDOM FUNDERS",
    ],
}


def classify_file(filename: str) -> str:
    """Classifica um arquivo baseado em seu nome."""
    filename_upper = filename.upper()

    # Primeiro verificar padrões específicos
    for source, patterns in PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, filename_upper, re.IGNORECASE):
                return source

    # Verificação adicional para G4 (formato M1 A1 sem underscore)
    if re.search(r"\. M\d+ A\d+ -", filename):
        return "G4_EDUCACAO"

    # Verificação para Full Sales System (português com MOD/AULA)
    if re.search(r"MOD \d+.*AULA|AULA \d+", filename, re.IGNORECASE):
        return "FULL_SALES_SYSTEM"

    # Se tem data no final e é inglês, provavelmente Jeremy Haynes
    if re.search(r"\d{1,2}-\d{1,2}-\d{2}\.txt$", filename):
        return "JEREMY_HAYNES"

    return "UNKNOWN"


def get_content_type(subdir: str) -> str:
    """Mapeia subdiretório para tipo de conteúdo."""
    mapping = {
        "BLUEPRINTS": "BLUEPRINTS",
        "COURSES": "COURSES",
        "MARKETING": "MARKETING",
        "MASTERMINDS": "MASTERMINDS",
        "OUTROS": "OUTROS",
        "PODCASTS": "PODCASTS",
        "SCRIPTS": "SCRIPTS",
        "VSL": "VSL",
        "YOUTUBE": "PODCASTS",  # Tratar YouTube como podcasts
    }
    return mapping.get(subdir, "COURSES")


def main():
    """Classifica e move arquivos de _UNKNOWN."""
    if not UNKNOWN_DIR.exists():
        print("Diretório _UNKNOWN não encontrado!")
        return

    # Estatísticas
    stats = {k: 0 for k in DESTINATIONS.keys()}
    stats["UNKNOWN"] = 0
    moved = []
    failed = []

    # Criar diretórios de destino se não existirem
    for dest_path in DESTINATIONS.values():
        dest_path.mkdir(parents=True, exist_ok=True)

    # Processar todos os arquivos .txt em _UNKNOWN
    for subdir in UNKNOWN_DIR.iterdir():
        if not subdir.is_dir():
            continue

        subdir_name = subdir.name
        content_type = get_content_type(subdir_name)

        for file in subdir.glob("*.txt"):
            filename = file.name
            source = classify_file(filename)

            if source == "UNKNOWN":
                stats["UNKNOWN"] += 1
                failed.append((str(file), "Não classificado"))
                continue

            # Destino
            dest_base = DESTINATIONS[source]
            dest_dir = dest_base / content_type
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / filename

            # Mover arquivo
            try:
                if not dest_file.exists():
                    shutil.move(str(file), str(dest_file))
                    stats[source] += 1
                    moved.append((str(file), str(dest_file)))
                    print(f"[OK] {source}: {filename}")
                else:
                    print(f"[SKIP] Ja existe: {dest_file}")
                    failed.append((str(file), "Já existe no destino"))
            except Exception as e:
                print(f"[ERRO] Erro ao mover {filename}: {e}")
                failed.append((str(file), str(e)))

    # Relatório
    print("\n" + "=" * 60)
    print("RELATÓRIO DE CLASSIFICAÇÃO")
    print("=" * 60)
    for source, count in stats.items():
        if count > 0:
            print(f"{source}: {count} arquivos")
    print(f"\nTotal movidos: {len(moved)}")
    print(f"Não classificados: {stats['UNKNOWN']}")
    print(f"Falhas: {len([f for f in failed if f[1] != 'Não classificado'])}")

    if failed:
        print("\n" + "-" * 60)
        print("ARQUIVOS NÃO CLASSIFICADOS:")
        print("-" * 60)
        for path, reason in failed:
            if reason == "Não classificado":
                print(f"  - {Path(path).name}")


if __name__ == "__main__":
    main()
