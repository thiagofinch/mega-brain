# SKILL-PYTHON-MEGABRAIN
## Padrões de Código Python do Mega Brain

> **Auto-Trigger:** Criação/edição de arquivos .py no projeto
> **Keywords:** "script", "python", "código", "função", "automação"
> **Prioridade:** ALTA

---

## PROPÓSITO

Garantir que todo código Python do Mega Brain siga padrões de:
- Legibilidade e manutenibilidade
- Documentação inline
- Tratamento de erros
- Integração com o ecossistema

---

## QUANDO USAR

### ✅ USAR quando:
- Criar novos scripts Python
- Modificar scripts existentes
- Criar funções de processamento
- Desenvolver integrações

### ❌ NÃO USAR quando:
- Scripts one-off descartáveis
- Notebooks exploratórios
- Código de terceiros

---

## REGRAS OBRIGATÓRIAS

### Estrutura de Script

```python
#!/usr/bin/env python3
"""
[NOME DO SCRIPT] - [Descrição em uma linha]
============================================

[Descrição mais detalhada do que o script faz]

Uso:
    python script.py [argumentos]

Exemplos:
    python script.py --input arquivo.txt
    python script.py --process-all

Dependências:
    pip install [pacotes necessários]

Variáveis de ambiente:
    VAR_NAME - Descrição da variável
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

***REMOVED***=================================
# CONFIGURAÇÃO
***REMOVED***=================================

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "system" / "config.json"

***REMOVED***=================================
# FUNÇÕES AUXILIARES
***REMOVED***=================================

def funcao_auxiliar():
    """Descrição da função."""
    pass

***REMOVED***=================================
# FUNÇÕES PRINCIPAIS
***REMOVED***=================================

def funcao_principal():
    """Descrição da função principal."""
    pass

***REMOVED***=================================
# MAIN
***REMOVED***=================================

def main():
    """Entry point do script."""
    parser = argparse.ArgumentParser(description="Descrição")
    parser.add_argument("--flag", help="Descrição da flag")
    args = parser.parse_args()
    
    # Lógica principal
    pass

if __name__ == "__main__":
    main()
```

### Naming Conventions

| Tipo | Convenção | Exemplo |
|------|-----------|---------|
| Arquivos | snake_case | `process_video.py` |
| Funções | snake_case | `def extract_insights():` |
| Classes | PascalCase | `class InsightExtractor:` |
| Constantes | UPPER_SNAKE | `MAX_RETRIES = 3` |
| Variáveis | snake_case | `chunk_count = 0` |

### Docstrings Obrigatórias

```python
def process_content(
    content: str,
    source_id: str,
    options: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Processa conteúdo e extrai insights.
    
    Args:
        content: Texto bruto para processar
        source_id: ID da fonte (ex: "CG003")
        options: Configurações opcionais
            - max_chunks: Máximo de chunks (default: 100)
            - min_confidence: Confiança mínima (default: 0.7)
    
    Returns:
        Dict contendo:
            - insights: Lista de insights extraídos
            - metadata: Informações do processamento
            - errors: Erros encontrados (se houver)
    
    Raises:
        ValueError: Se content estiver vazio
        ProcessingError: Se extração falhar
    
    Example:
        >>> result = process_content("texto aqui", "CG003")
        >>> print(result["insights"])
    """
    pass
```

### Type Hints Obrigatórios

```python
# ✅ Correto
def get_insights(source_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    pass

# ❌ Incorreto
def get_insights(source_id, limit=10):
    pass
```

### Tratamento de Erros

```python
# Padrão de try/except
try:
    result = process_file(path)
except FileNotFoundError:
    print(f"❌ Arquivo não encontrado: {path}")
    return None
except json.JSONDecodeError as e:
    print(f"❌ JSON inválido: {e}")
    return None
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    raise

# Logging de progresso
print(f"📥 Processando: {filename}")
print(f"   ├── Chunks: {chunk_count}")
print(f"   ├── Insights: {insight_count}")
print(f"   └── Status: ✅ Concluído")
```

### Emojis de Status Padronizados

| Emoji | Significado | Uso |
|-------|-------------|-----|
| 📥 | Input/Início | Recebendo dados |
| 🔄 | Processando | Em andamento |
| ✅ | Sucesso | Concluído com sucesso |
| ❌ | Erro | Falha |
| ⚠️ | Aviso | Atenção necessária |
| 📊 | Métricas | Estatísticas |
| 💾 | Salvo | Arquivo gravado |
| 🔍 | Busca | Pesquisando |

### Paths do Projeto

```python
from pathlib import Path

# Sempre usar Path, nunca strings concatenadas
PROJECT_ROOT = Path(__file__).parent.parent

# Paths padrão do Mega Brain
PATHS = {
    "inbox": PROJECT_ROOT / "inbox",
    "processing": PROJECT_ROOT / "processing",
    "knowledge": PROJECT_ROOT / "knowledge",
    "playbooks": PROJECT_ROOT / "knowledge/playbooks",
    "system": PROJECT_ROOT / "system",
    "agents": PROJECT_ROOT / "agents",
    "logs": PROJECT_ROOT / "logs",
}
```

### JSON Handling

```python
def load_json(path: Path) -> Dict:
    """Carrega JSON com tratamento de erro."""
    if not path.exists():
        return {}
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: Dict, path: Path, indent: int = 2) -> None:
    """Salva JSON com formatação."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    
    print(f"💾 Salvo: {path}")
```

### CLI com Argparse

```python
def main():
    parser = argparse.ArgumentParser(
        description="Descrição do script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python script.py --process arquivo.txt
    python script.py --all --verbose
        """
    )
    
    # Argumentos posicionais
    parser.add_argument("input", nargs="?", help="Arquivo de entrada")
    
    # Flags
    parser.add_argument("--all", "-a", action="store_true", help="Processar todos")
    parser.add_argument("--verbose", "-v", action="store_true", help="Output detalhado")
    parser.add_argument("--output", "-o", type=Path, help="Diretório de saída")
    
    args = parser.parse_args()
```

---

## PADRÕES DE OUTPUT

### Relatório de Processamento

```python
def print_report(stats: Dict) -> None:
    """Imprime relatório padronizado."""
    print("\n" + "="*60)
    print("📊 RELATÓRIO DE PROCESSAMENTO")
    print("="*60)
    print(f"""
┌─────────────────────────────────────────────────────────┐
│  Arquivos processados: {stats['processed']:>5}                         │
│  Insights extraídos:   {stats['insights']:>5}                         │
│  Erros:                {stats['errors']:>5}                         │
│  Tempo total:          {stats['time']:.2f}s                        │
└─────────────────────────────────────────────────────────┘
""")
```

---

## ANTI-PATTERNS (NUNCA FAZER)

1. ❌ Funções sem docstring
2. ❌ Código sem type hints
3. ❌ `except:` genérico sem especificar exceção
4. ❌ Paths com strings concatenadas (`"dir/" + "file"`)
5. ❌ Print sem contexto (`print(x)`)
6. ❌ Variáveis de uma letra (exceto loops)
7. ❌ Imports dentro de funções (exceto lazy loading)
8. ❌ Hardcoded paths absolutos

---

## CHECKLIST PRÉ-ENTREGA

- [ ] Docstring no topo do arquivo
- [ ] Todas funções com docstring
- [ ] Type hints em todas funções
- [ ] Tratamento de erros apropriado
- [ ] Paths usando pathlib.Path
- [ ] Encoding UTF-8 em file operations
- [ ] CLI com argparse se aplicável
- [ ] Emojis de status consistentes

---

## META-INFORMAÇÃO

- **Versão:** 1.0.0
- **Domínio:** Código
- **Prioridade:** ALTA
- **Dependências:** Nenhuma
