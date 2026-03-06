# RESTORE-AND-INDEX.md
# Instruções para Restauração de Arquivos e Criação do Sistema de Indexação

---

## CONTEXTO DO PROBLEMA

Durante a Fase 2.5 (Deduplicação), arquivos foram movidos de suas pastas principais para pastas de backup (`_DUPLICATAS_*`, `_DEDUP_BACKUP`, etc.). Isso quebrou a rastreabilidade porque:

1. Batches referenciam TAGs (ex: `JH-ST-0002`)
2. TAGs apontam para subpastas específicas (ex: `inbox/JEREMY HAYNES/SALES-TRAINING/`)
3. Essas subpastas estão VAZIAS - arquivos estão nos backups
4. Agentes não conseguem resolver TAG → arquivo original

---

## PARTE 1: RESTAURAÇÃO VIA GIT

### 1.1 Verificar Estado Atual

```bash
# Verificar quantos arquivos estão "deletados" (movidos)
# From the project root
git status --porcelain | grep "^ D" | wc -l

# Ver quais pastas estão afetadas
git status --porcelain | grep "inbox" | head -20
```

**Resultado esperado:** ~1.248 arquivos marcados como deletados

### 1.2 Executar Restauração

```bash
# COMANDO PRINCIPAL - Restaura todos os arquivos do INBOX
# From the project root
git restore "inbox/"
```

**O que acontece:**
- Arquivos voltam para suas pastas originais
- Pastas de backup (`_DUPLICATAS_*`) continuam existindo com suas cópias
- Nenhum dado é perdido

### 1.3 Validar Restauração

```bash
# Verificar que arquivos voltaram
cd inbox

# Contar por fonte principal
echo "=== ALEX HORMOZI ===" && find "ALEX HORMOZI" -type f | wc -l
echo "=== COLE GORDON ===" && find "COLE GORDON" -type f | wc -l
echo "=== JEREMY HAYNES ===" && find "JEREMY HAYNES" -type f | wc -l
echo "=== JEREMY MINER ===" && find "JEREMY MINER" -type f | wc -l
```

**Resultado esperado:** Cada pasta deve ter dezenas/centenas de arquivos

### 1.4 Verificar Integridade das TAGs

```bash
# Contar arquivos COM TAG (formato [XXX-NNNN])
cd inbox
find . -name "*\[*-*\]*" -type f | wc -l

# Listar alguns exemplos
find . -name "*\[JH-*" -type f | head -10
find . -name "*\[JM-*" -type f | head -10
```

**Resultado esperado:** ~727 arquivos com TAG no nome

---

## PARTE 2: LIMPEZA DOS BACKUPS

### 2.1 Mover Backups para ARCHIVE

Após restauração confirmada, mover pastas de backup para não poluir o INBOX:

```bash
# From the project root

# Criar pasta de archive para backups de deduplicação
mkdir -p "archive/dedup-backups-2026-01-08"

# Mover todas as pastas de backup
mv "inbox/_DEDUP_BACKUP" "archive/dedup-backups-2026-01-08/"
mv "inbox/_DUPLICATAS_1PARA1_2026-01-08" "archive/dedup-backups-2026-01-08/"
mv "inbox/_DUPLICATAS_FINAL" "archive/dedup-backups-2026-01-08/"
mv "inbox/_DUPLICATAS_FINAL_V2" "archive/dedup-backups-2026-01-08/"
mv "inbox/_DUPLICATAS_REMOVIDAS" "archive/dedup-backups-2026-01-08/"
mv "inbox/_EXTRAS_ORFAOS_2026-01-08" "archive/dedup-backups-2026-01-08/"
mv "inbox/_EXTRAS_REMOVIDOS_2026-01-08" "archive/dedup-backups-2026-01-08/"
mv "inbox/_EXTRAS_RIGOROSO_2026-01-08" "archive/dedup-backups-2026-01-08/"
mv "inbox/_EXTRAS_SEM_MATCH_2026-01-08" "archive/dedup-backups-2026-01-08/"
mv "inbox/_LIMPEZA_FINAL" "archive/dedup-backups-2026-01-08/"
mv "inbox/_UNKNOWN" "archive/dedup-backups-2026-01-08/"
```

**MANTER no INBOX:**
- `_TEMPLATES/` - templates de transcrição
- `_BACKUP_COLE_GORDON_CLEANUP/` - se estiver vazio, pode deletar

### 2.2 Criar README no Archive

```bash
cat > "archive/dedup-backups-2026-01-08/README.md" << 'EOF'
# Backups de Deduplicação - 2026-01-08

## Contexto
Durante a Fase 2.5 (Deduplicação), arquivos foram movidos para estas pastas
para identificar e remover duplicatas.

## Conteúdo
- `_DEDUP_BACKUP/` - Backup inicial antes de deduplicação
- `_DUPLICATAS_*` - Arquivos identificados como duplicatas
- `_EXTRAS_*` - Arquivos extras ou sem match na planilha
- `_LIMPEZA_FINAL/` - Resultado da limpeza final

## Status
- Data: 2026-01-08
- Arquivos originais: RESTAURADOS para inbox via git restore
- Estes backups: Mantidos para referência histórica

## Ação
Estes arquivos podem ser DELETADOS após confirmação de que:
1. Todos os originais estão em inbox
2. TAG-RESOLVER.json foi criado e validado
3. Sistema de rastreabilidade está funcionando
EOF
```

---

## PARTE 3: VALIDAÇÃO FINAL

### 3.1 Checklist de Validação

Execute e confirme cada item:

```bash
# From the project root

# 1. Git status limpo para INBOX
echo "=== GIT STATUS ==="
git status --porcelain | grep "inbox" | wc -l
# Esperado: 0 (nenhuma mudança pendente)

# 2. Pastas principais têm arquivos
echo "=== CONTAGEM POR FONTE ==="
for dir in "inbox/alex hormozi" \
           "inbox/COLE GORDON" \
           "inbox/JEREMY HAYNES" \
           "inbox/JEREMY MINER" \
    count=$(find "$dir" -type f 2>/dev/null | wc -l)
    echo "$dir: $count arquivos"
done

# 3. Arquivos com TAG existem
echo "=== ARQUIVOS COM TAG ==="
find "inbox" -name "*\[*-*\]*" -type f | wc -l
# Esperado: ~727

# 4. Backups foram movidos
echo "=== BACKUPS NO ARCHIVE ==="
ls -la "archive/dedup-backups-2026-01-08/" | wc -l
# Esperado: ~12 itens (10 pastas + README + .)

# 5. INBOX não tem mais pastas _*
echo "=== PASTAS _ NO INBOX ==="
ls -d "inbox/_"* 2>/dev/null | grep -v "_TEMPLATES" | wc -l
# Esperado: 0 ou 1 (apenas _TEMPLATES deve restar)
```

### 3.2 Resultado Esperado

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  VALIDAÇÃO PÓS-RESTAURAÇÃO                                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  [✓] Git status limpo para inbox                                          ║
║  [✓] ALEX HORMOZI: ~19 arquivos                                              ║
║  [✓] COLE GORDON: ~120+ arquivos                                             ║
║  [✓] JEREMY HAYNES: ~253 arquivos                                            ║
║  [✓] JEREMY MINER: ~153 arquivos                                             ║
║  [✓] Arquivos com TAG: ~727                                                  ║
║  [✓] Backups movidos para archive                                         ║
║  [✓] INBOX sem pastas _* (exceto _TEMPLATES)                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## PRÓXIMO PASSO

Após completar esta parte, execute as instruções em:
**`TAG-RESOLVER-IMPLEMENTATION.md`**

Isso criará o sistema de resolução TAG → Path que está faltando.
