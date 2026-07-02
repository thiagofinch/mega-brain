"""ingest.py -- /ingerir-files Orchestrator entry-point."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SKILL_DIR))

from engine.config import get_config

for _key in [
    "FIREFLIES_API_KEY", "FIREFLIES_API_KEY_SECONDARY",
    "ZAPI_INSTANCE_ID", "ZAPI_TOKEN", "ZAPI_CLIENT_TOKEN",
    "ZAPI_TARGET_PHONE", "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID",
    "OPENAI_API_KEY",
]:
    _val = get_config(_key, "")
    if _val and not os.environ.get(_key):
        os.environ[_key] = _val

from briefing import generate_briefing, scan_recent_calls  # noqa: E402
from dashboard import render_dashboard  # noqa: E402
from multi_fireflies import build_unified_view, discover_for_dashboard, run_multi_account  # noqa: E402
from state import load_state, save_state, stamp_jarvis_run  # noqa: E402


def health_check(skip_zapi: bool = False, skip_audio: bool = False) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    # FIREFLIES_API_KEY obrigatorio (account primario)
    val = os.environ.get("FIREFLIES_API_KEY", "")
    checks.append({"name": "env:FIREFLIES_API_KEY", "ok": bool(val), "detail": "account=primary" if val else "MISSING (BLOCKING)", "required": True})
    # FIREFLIES_API_KEY_SECONDARY opcional (warning apenas)
    val = os.environ.get("FIREFLIES_API_KEY_SECONDARY", "")
    checks.append({"name": "env:FIREFLIES_API_KEY_SECONDARY", "ok": True, "detail": "account=secondary" if val else "MISSING (optional - secondary account will be skipped)", "required": False, "warning": not bool(val)})
    if not skip_zapi:
        for env_key in ["ZAPI_INSTANCE_ID", "ZAPI_TOKEN", "ZAPI_CLIENT_TOKEN", "ZAPI_TARGET_PHONE"]:
            checks.append({"name": f"env:{env_key}", "ok": bool(os.environ.get(env_key, "")), "detail": "set" if os.environ.get(env_key) else "MISSING", "required": True})
    if not skip_audio:
        for env_key in ["ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID"]:
            checks.append({"name": f"env:{env_key}", "ok": bool(os.environ.get(env_key, "")), "detail": "set" if os.environ.get(env_key) else "MISSING", "required": True})
    state = load_state()
    checks.append({"name": "state:loaded", "ok": True, "detail": f"processed={len(state.jarvis.processed_meeting_ids)}", "required": True})
    # Apenas required checks afetam o ok overall
    required_ok = all(c["ok"] for c in checks if c.get("required", True))
    return {"ok": required_ok, "checks": checks}


def render_health(result: dict[str, Any]) -> str:
    lines = ["", "=" * 70, "  PHASE 0 -- HEALTH CHECK", "=" * 70]
    for c in result["checks"]:
        status = "OK" if c["ok"] else "FAIL"
        lines.append(f"  [{status:^4}]  {c['name']:<35} {c['detail']}")
    lines.append("=" * 70)
    lines.append(f"  Status: {'READY' if result['ok'] else 'BLOCKED'}")
    lines.append("=" * 70)
    return "\n".join(lines)


def scan_inbox_for_meet_ids() -> list[str]:
    inbox = REPO_ROOT / "knowledge/business/inbox"
    if not inbox.exists():
        return []
    pattern = re.compile(r"\[MEET-(\d+)\]")
    return sorted({f"MEET-{m.group(1)}" for f in inbox.iterdir() if (m := pattern.search(f.name))})


def compute_pending_for_jarvis() -> dict[str, Any]:
    state = load_state()
    inbox_ids = scan_inbox_for_meet_ids()
    processed = set(state.jarvis.processed_meeting_ids)
    pending = [mid for mid in inbox_ids if mid not in processed]
    return {"inbox_total": len(inbox_ids), "processed_total": len(processed), "pending_count": len(pending), "pending_ids": pending}


def trigger_process_jarvis(pending_ids: list[str], dry_run: bool = False) -> dict[str, Any]:
    """Phase 4: blocking RAG rebuild (Art. XV gate).

    Bloqueia ate Phase 4.5 RAG indexation completar. Briefing/audio so
    podem rodar depois disso. Atalho prag: rebuild(bucket='business')
    ja escaneia o bucket inteiro -- nao precisa subprocess per-file.

    Story: INGERIR-FILES-1.1 AC2.
    """
    if dry_run:
        return {"skipped_dry_run": True, "rag_ok": True, "would_process": len(pending_ids)}
    if not pending_ids:
        return {"processed": 0, "rag_ok": True, "note": "nothing to process -- RAG skipped"}

    inbox = REPO_ROOT / "knowledge/business/inbox"

    # 4a: count physical files in bucket
    files_in_bucket = 0
    for mid in pending_ids:
        matches = [f for f in inbox.rglob(f"*{mid}*") if f.is_file() and f.suffix == ".txt"]
        if matches:
            files_in_bucket += 1
    print(f"  [4a] {files_in_bucket}/{len(pending_ids)} arquivos novos confirmados em {inbox.name}/", flush=True)

    # 4b: RAG rebuild blocking (Constitution Art. XV)
    print("  [4b] RAG rebuild bucket=business (BM25 + vetores OpenAI)...", flush=True)
    import time as _time
    rebuild_result: dict[str, Any] = {}
    t0 = _time.monotonic()
    try:
        from engine.intelligence.rag.rebuild import rebuild
        rebuild_result = rebuild(bucket="business", skip_vectors=False)
        biz = rebuild_result.get("business", {})
        dt = _time.monotonic() - t0
        print(f"  [4b] RAG done -- chunks={biz.get('chunks', 0)} dur={dt:.1f}s", flush=True)
    except Exception as e:
        rebuild_result = {"error": str(e)}
        dt = _time.monotonic() - t0
        print(f"  [4b] RAG FAILED apos {dt:.1f}s: {e}", flush=True)

    rag_ok = "error" not in rebuild_result
    if rag_ok:
        state = load_state()
        stamp_jarvis_run(state, pending_ids)
        save_state(state)

    return {
        "files_in_bucket": files_in_bucket,
        "rag_rebuild": rebuild_result,
        "rag_ok": rag_ok,
        "processed": files_in_bucket if rag_ok else 0,
    }


def cmd_dashboard(args: argparse.Namespace) -> int:
    print(render_health(health_check(skip_zapi=True, skip_audio=True)))
    print("\nDescobrindo calls...", flush=True)
    discovery = discover_for_dashboard(args.accounts)
    if not discovery.get("success", False):
        return 1
    rows = build_unified_view(discovery)
    print(render_dashboard(rows))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    started_at = datetime.now(UTC)
    today_str = started_at.strftime("%Y-%m-%d")
    output_dir = REPO_ROOT / "outputs/founder-briefings" / today_str
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {"started_at": started_at.isoformat(), "phases": {}}

    h = health_check(skip_zapi=args.skip_zapi, skip_audio=args.skip_audio)
    print(render_health(h))
    if not h["ok"] and not args.force:
        return 1

    print("\n=== PHASE 2 MULTI-ACCOUNT SYNC ===")
    if args.dry_run:
        sync_result = {"skipped_dry_run": True}
    else:
        sync_result = run_multi_account(args.accounts)
        print(f"  Total NEW: {sync_result.get('total_new', 0)}")
    report["phases"]["phase_2_sync"] = sync_result

    print("\n=== PHASE 3 DIFF ===")
    diff = compute_pending_for_jarvis()
    print(f"  Inbox: {diff['inbox_total']}  Processed: {diff['processed_total']}  Pending: {diff['pending_count']}")
    report["phases"]["phase_3_diff"] = diff

    print("\n=== PHASE 4 PIPELINE (RAG rebuild bucket=business) ===")
    if args.skip_pipeline:
        print("  SKIPPED por --skip-pipeline -- usando estado RAG atual.")
        jr = {"skipped": True, "rag_ok": True, "processed": 0}
    else:
        jr = trigger_process_jarvis(diff["pending_ids"], args.dry_run)
        if not jr.get("rag_ok", True) and not args.force:
            print(f"  ABORT: RAG rebuild falhou -- {jr.get('rag_rebuild', {}).get('error', '?')}")
            print("  Briefing/audio NAO disparam ate RAG completar (use --force para ignorar).")
            report["phases"]["phase_4_pipeline"] = jr
            return 1
    report["phases"]["phase_4_pipeline"] = jr

    print(f"\n=== PHASE 5 BRIEFING ({args.window_days}d) ===")
    calls = scan_recent_calls(args.window_days)
    bm = generate_briefing(calls, output_dir, args.window_days)
    print(f"  Briefing: {bm['briefing_path']}")
    print(f"  Score: {bm['alignment_score']}/100 ({bm['label']})")
    report["phases"]["phase_5_briefing"] = bm

    print("\n=== PHASE 6 TTS + Z-API ===")
    if args.dry_run or (args.skip_zapi and args.skip_audio):
        delivery = {"skipped": True}
    else:
        from tts_zapi import deliver_briefing
        delivery = deliver_briefing(output_dir, skip_audio=args.skip_audio, skip_zapi=args.skip_zapi)
        print(f"  Audio: {delivery.get('audio_path')}")
        print(f"  TTS OK: {delivery.get('tts_ok')}  Z-API OK: {delivery.get('zapi_ok')}")
        # AC4: surface tts_error in run-report
        if not delivery.get("tts_ok", True):
            err = delivery.get("tts_error", "(no detail)")
            print(f"  [TTS ERROR] {err[:200]}")
            report["partial_success"] = True
            report["tts_error"] = err
    report["phases"]["phase_6_delivery"] = delivery

    report["finished_at"] = datetime.now(UTC).isoformat()
    report["duration_seconds"] = (datetime.now(UTC) - started_at).total_seconds()
    (output_dir / "run-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nCONCLUIDO em {report['duration_seconds']:.1f}s  Output: {output_dir}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    print(json.dumps(load_state().to_dict(), indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="ingerir-files")
    sub = parser.add_subparsers(dest="cmd")
    sp_d = sub.add_parser("dashboard")
    sp_d.add_argument("--accounts", nargs="+", default=None)
    sp_r = sub.add_parser("run")
    sp_r.add_argument("--accounts", nargs="+", default=None)
    sp_r.add_argument("--window-days", type=int, default=7)
    sp_r.add_argument("--dry-run", action="store_true")
    sp_r.add_argument("--skip-zapi", action="store_true")
    sp_r.add_argument("--skip-audio", action="store_true")
    sp_r.add_argument("--skip-pipeline", action="store_true", help="Pula Phase 4 (RAG rebuild) -- usa estado atual")
    sp_r.add_argument("--force", action="store_true")
    sub.add_parser("status")

    args = parser.parse_args()
    if not args.cmd:
        args = parser.parse_args(["dashboard"])

    handlers = {"dashboard": cmd_dashboard, "run": cmd_run, "status": cmd_status}
    handler = handlers.get(args.cmd)
    if handler is None:
        parser.print_help()
        return 2
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
