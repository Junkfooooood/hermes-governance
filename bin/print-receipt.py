#!/usr/bin/env python3
"""Token Receipt Printer — Hermes daily usage in thermal receipt style.

Reads token/cost data from Hermes state.db or Claude Code transcripts,
renders an ASCII receipt inspired by Hchen1218/token-receipt.

Supports:
  - Terminal preview (default)
  - ESC/POS thermal printer output (--printer)
  - HTML export (--html)

Usage:
  python3 bin/print-receipt.py              # terminal preview, today
  python3 bin/print-receipt.py --days 7     # weekly summary
  python3 bin/print-receipt.py --printer    # send to USB thermal printer
  python3 bin/print-receipt.py --html out.html

Dependencies:
  - python-escpos (optional, only for --printer mode)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import csv
import os
import sqlite3
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WIDTH = 48  # 58mm thermal printer standard
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
CLAUDE_HOME = Path.home() / ".claude"
DB_PATH = HERMES_HOME / "state.db"

# ---------------------------------------------------------------------------
# Pricing table (per million tokens)
# ---------------------------------------------------------------------------

# Prices in CNY unless noted. Keys are model name substrings (lowercase).
PRICING: Dict[str, Dict[str, float]] = {
    # Xiaomi MiMo (source: platform.xiaomimimo.com)
    "mimo": {
        "currency": "CNY",
        "input": 2.0,           # ¥2/M — text input
        "output": 12.0,         # ¥12/M — text output
        "cache_read": 0.4,      # ¥0.4/M — cache hit
        "cache_write": 2.0,     # ¥2/M — cache miss (same as input)
        "output_cache": 1.5,    # ¥1.5/M — output cache
        "note": "MiMo-v2.5-Pro",
    },
    # DeepSeek V4 Flash (source: api-docs.deepseek.com, 2026-04-26)
    "deepseek-chat": {
        "currency": "USD",
        "input": 0.14,
        "output": 0.28,
        "cache_read": 0.0028,
        "cache_write": 0.14,
        "note": "DeepSeek-V4-Flash",
    },
    "deepseek-v4-flash": {
        "currency": "USD",
        "input": 0.14,
        "output": 0.28,
        "cache_read": 0.0028,
        "cache_write": 0.14,
        "note": "DeepSeek-V4-Flash",
    },
    "deepseek-reasoner": {
        "currency": "USD",
        "input": 0.55,
        "output": 2.19,
        "cache_read": 0.0028,
        "cache_write": 0.55,
        "note": "DeepSeek-V4-Flash (thinking)",
    },
    "deepseek-v4-pro": {
        "currency": "USD",
        "input": 0.435,       # 75% discount until 2026/5/31
        "output": 0.87,
        "cache_read": 0.003625,
        "cache_write": 0.435,
        "note": "DeepSeek-V4-Pro (75% off)",
    },
    # Anthropic Claude (USD, for reference)
    "claude-sonnet": {
        "currency": "USD",
        "input": 3.0,
        "output": 15.0,
        "cache_read": 0.30,
        "cache_write": 3.75,
        "note": "Claude Sonnet",
    },
    "claude-opus": {
        "currency": "USD",
        "input": 15.0,
        "output": 75.0,
        "cache_read": 1.50,
        "cache_write": 18.75,
        "note": "Claude Opus",
    },
    "claude-haiku": {
        "currency": "USD",
        "input": 0.80,
        "output": 4.0,
        "cache_read": 0.08,
        "cache_write": 1.0,
        "note": "Claude Haiku",
    },
}


def lookup_pricing(model: str) -> Optional[Dict[str, Any]]:
    """Find pricing entry for a model name."""
    m = model.lower()
    for key, pricing in PRICING.items():
        if key in m:
            return pricing
    return None


def calculate_cost(
    pricing: Dict[str, Any],
    input_tokens: int,
    output_tokens: int,
    cache_read: int = 0,
    cache_write: int = 0,
) -> float:
    """Calculate total cost from pricing and token counts."""
    per_m = 1_000_000
    cost = (
        input_tokens / per_m * pricing["input"]
        + output_tokens / per_m * pricing["output"]
        + cache_read / per_m * pricing["cache_read"]
        + cache_write / per_m * pricing["cache_write"]
    )
    return cost

# Snarky footer pool (Chinese, inspired by token-receipt)
FOOTERS = [
    "结果很体面，账单更诚实。",
    "看起来很轻松，付起来不是。",
    "事做完了，单也做出来了。",
    "Token 用掉了，钱包记住了。",
    "推理不免费，犹豫更贵。",
    "Bug 修完了，费用继承了。",
    "最后一版这个词，本来就不诚实。",
    "上下文撑住了，预算先躺下了。",
    "模型记住了很多，钱包也记住了。",
    "输出很干净，小票知道为什么。",
    "钱烧掉了，事情推进了。",
    "这轮不算白跑，但也不便宜。",
    "画面稳了，预算死了。",
    "补丁合上了，钱包裂开了。",
    "缓存救了一点，不够救你。",
    "思考得很认真，结账也很认真。",
    "版本更好了，现金流更坏了。",
    "交付完成，余款阵亡。",
    "你花的是明白钱。",
    "小票出来了，这轮不算白跑。",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class UsageSnapshot:
    """Aggregated token usage for a time period."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0      # cache hit
    cache_write_tokens: int = 0     # cache miss / creation
    reasoning_tokens: int = 0
    total_tokens: int = 0
    session_count: int = 0
    message_count: int = 0
    api_calls: int = 0
    estimated_cost: float = 0.0
    cost_currency: str = "CNY"
    provider: str = "unknown"
    model: str = "unknown"
    models_used: Optional[List[str]] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    pricing_note: str = ""

    def __post_init__(self):
        if self.models_used is None:
            self.models_used = []
        if self.total_tokens == 0:
            self.total_tokens = (
                self.input_tokens + self.output_tokens +
                self.cache_read_tokens + self.cache_write_tokens +
                self.reasoning_tokens
            )


# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------


def load_from_hermes(db_path: Path, days: int) -> Optional[UsageSnapshot]:
    """Load aggregated usage from Hermes state.db."""
    if not db_path.exists():
        return None

    cutoff = time.time() - (days * 86400)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(
            """SELECT
                 COUNT(*) as session_count,
                 COALESCE(SUM(message_count), 0) as message_count,
                 COALESCE(SUM(input_tokens), 0) as input_tokens,
                 COALESCE(SUM(output_tokens), 0) as output_tokens,
                 COALESCE(SUM(cache_read_tokens), 0) as cache_read_tokens,
                 COALESCE(SUM(cache_write_tokens), 0) as cache_write_tokens,
                 COALESCE(SUM(estimated_cost_usd), 0) as estimated_cost,
                 COALESCE(SUM(api_call_count), 0) as api_calls,
                 MIN(started_at) as earliest,
                 MAX(started_at) as latest
               FROM sessions WHERE started_at >= ?""",
            (cutoff,),
        ).fetchone()

        if not rows or rows["session_count"] == 0:
            return None

        # Get model breakdown
        models = conn.execute(
            """SELECT model, COUNT(*) as cnt,
                      SUM(input_tokens + output_tokens) as tokens
               FROM sessions WHERE started_at >= ?
               GROUP BY model ORDER BY tokens DESC""",
            (cutoff,),
        ).fetchall()

        primary_model = models[0]["model"] if models else "unknown"
        model_list = [r["model"] for r in models if r["model"]]

        # Get provider from most-used session
        provider_row = conn.execute(
            """SELECT billing_provider FROM sessions
               WHERE started_at >= ? AND billing_provider IS NOT NULL
               ORDER BY input_tokens + output_tokens DESC LIMIT 1""",
            (cutoff,),
        ).fetchone()
        provider = (provider_row["billing_provider"] if provider_row else "unknown") or "unknown"

        # Try to calculate cost from pricing table if DB has no cost
        est_cost = rows["estimated_cost"]
        currency = "USD"
        note = ""
        if not est_cost:
            pricing = lookup_pricing(primary_model)
            if pricing:
                est_cost = calculate_cost(
                    pricing,
                    input_tokens=rows["input_tokens"],
                    output_tokens=rows["output_tokens"],
                    cache_read=rows["cache_read_tokens"],
                    cache_write=rows["cache_write_tokens"],
                )
                currency = pricing["currency"]
                note = pricing.get("note", "")

        return UsageSnapshot(
            input_tokens=rows["input_tokens"],
            output_tokens=rows["output_tokens"],
            cache_read_tokens=rows["cache_read_tokens"],
            cache_write_tokens=rows["cache_write_tokens"],
            session_count=rows["session_count"],
            message_count=rows["message_count"],
            api_calls=rows["api_calls"],
            estimated_cost=est_cost,
            cost_currency=currency,
            provider=provider,
            model=primary_model,
            models_used=model_list,
            start_time=rows["earliest"],
            end_time=rows["latest"],
            pricing_note=note,
        )
    finally:
        conn.close()


def load_from_claude_transcripts(projects_dir: Path, days: int) -> Optional[UsageSnapshot]:
    """Load usage from Claude Code JSONL transcripts as fallback."""
    if not projects_dir.exists():
        return None

    cutoff = time.time() - (days * 86400)
    total_input = 0
    total_output = 0
    total_cache_read = 0    # cache hit
    total_cache_write = 0   # cache miss / creation
    total_reasoning = 0
    session_count = 0
    message_count = 0
    models_seen: Dict[str, int] = {}

    for jsonl_file in projects_dir.rglob("*.jsonl"):
        # Skip subagent files
        if "subagents" in jsonl_file.parts:
            continue

        mtime = jsonl_file.stat().st_mtime
        if mtime < cutoff:
            continue

        session_count += 1
        session_model = None

        try:
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Claude Code wraps messages in a "message" key
                    msg = entry.get("message", entry)

                    # Extract model info
                    model = msg.get("model") or entry.get("model") or entry.get("modelId")
                    if model:
                        session_model = model

                    # Extract usage from assistant messages
                    role = msg.get("role") or entry.get("role")
                    if role == "assistant":
                        message_count += 1
                        usage = msg.get("usage", {})
                        if usage:
                            total_input += usage.get("input_tokens", 0)
                            total_output += usage.get("output_tokens", 0)
                            total_cache_read += usage.get("cache_read_input_tokens", 0)
                            total_cache_write += usage.get("cache_creation_input_tokens", 0)
                            total_reasoning += usage.get("reasoning_tokens", 0)

            if session_model:
                models_seen[session_model] = models_seen.get(session_model, 0) + 1
        except (OSError, UnicodeDecodeError):
            continue

    if session_count == 0:
        return None

    # Pick most common model
    primary = max(models_seen, key=models_seen.get) if models_seen else "claude"

    # Detect provider from env or model name
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
    if "xiaomimimo" in base_url:
        provider = "xiaomi"
    elif "claude" in primary.lower():
        provider = "anthropic"
    elif "deepseek" in primary.lower():
        provider = "deepseek"
    else:
        provider = "unknown"

    # Calculate cost from pricing table
    pricing = lookup_pricing(primary)
    cost = 0.0
    currency = "CNY"
    note = ""
    if pricing:
        cost = calculate_cost(
            pricing,
            input_tokens=total_input,
            output_tokens=total_output,
            cache_read=total_cache_read,
            cache_write=total_cache_write,
        )
        currency = pricing["currency"]
        note = pricing.get("note", "")

    return UsageSnapshot(
        input_tokens=total_input,
        output_tokens=total_output,
        cache_read_tokens=total_cache_read,
        cache_write_tokens=total_cache_write,
        reasoning_tokens=total_reasoning,
        session_count=session_count,
        message_count=message_count,
        provider=provider,
        model=primary,
        models_used=list(models_seen.keys()),
        estimated_cost=cost,
        cost_currency=currency,
        pricing_note=note,
    )


def load_from_deepseek_csvs(cost_dir: Path, days: int) -> Optional[UsageSnapshot]:
    """Load DeepSeek usage from exported CSV files.

    Expects directory containing amount-YYYY-M.csv and cost-YYYY-M.csv files
    exported from platform.deepseek.com.
    """
    if not cost_dir.exists():
        return None

    from datetime import date, timedelta

    cutoff_date = date.today() - timedelta(days=days)
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_write = 0
    total_cost = 0.0
    models_seen: Dict[str, int] = {}
    request_count = 0
    days_with_data = set()

    # Find all amount CSV files
    for csv_file in sorted(cost_dir.rglob("amount-*.csv")):
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        row_date = date.fromisoformat(row["utc_date"])
                    except (ValueError, KeyError):
                        continue
                    if row_date < cutoff_date:
                        continue

                    model = row.get("model", "")
                    token_type = row.get("type", "")
                    amount = int(row.get("amount", 0) or 0)

                    days_with_data.add(row_date.isoformat())

                    if token_type == "output_tokens":
                        total_output += amount
                        models_seen[model] = models_seen.get(model, 0) + amount
                    elif token_type == "input_cache_hit_tokens":
                        total_cache_read += amount
                    elif token_type == "input_cache_miss_tokens":
                        total_input += amount
                    elif token_type == "request_count":
                        request_count += amount
        except (OSError, csv.Error):
            continue

    # Find all cost CSV files for actual cost
    for csv_file in sorted(cost_dir.rglob("cost-*.csv")):
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        row_date = date.fromisoformat(row["utc_date"])
                    except (ValueError, KeyError):
                        continue
                    if row_date < cutoff_date:
                        continue
                    cost = float(row.get("cost", 0) or 0)
                    total_cost += cost
        except (OSError, csv.Error):
            continue

    if not days_with_data:
        return None

    primary = max(models_seen, key=models_seen.get) if models_seen else "deepseek-v4-pro"

    return UsageSnapshot(
        input_tokens=total_input,
        output_tokens=total_output,
        cache_read_tokens=total_cache_read,
        cache_write_tokens=0,
        session_count=request_count,
        message_count=request_count,
        estimated_cost=total_cost,
        cost_currency="CNY",
        provider="deepseek",
        model=primary,
        models_used=list(models_seen.keys()),
        pricing_note="DeepSeek (平台实际费用)",
    )


def merge_snapshots(*snaps: Optional[UsageSnapshot]) -> UsageSnapshot:
    """Merge multiple UsageSnapshots into one aggregated result."""
    merged = UsageSnapshot()
    all_models = []
    for s in snaps:
        if not s:
            continue
        merged.input_tokens += s.input_tokens
        merged.output_tokens += s.output_tokens
        merged.cache_read_tokens += s.cache_read_tokens
        merged.cache_write_tokens += s.cache_write_tokens
        merged.reasoning_tokens += s.reasoning_tokens
        merged.session_count += s.session_count
        merged.message_count += s.message_count
        merged.api_calls += s.api_calls
        merged.estimated_cost += s.estimated_cost
        all_models.extend(s.models_used or [])

    # Dedupe models, preserve order
    seen = set()
    merged.models_used = []
    for m in all_models:
        if m not in seen:
            seen.add(m)
            merged.models_used.append(m)

    # Pick primary model (most tokens)
    if merged.models_used:
        merged.model = merged.models_used[0]
    merged.provider = "multi"
    merged.cost_currency = "CNY"
    merged.total_tokens = (
        merged.input_tokens + merged.output_tokens +
        merged.cache_read_tokens + merged.cache_write_tokens +
        merged.reasoning_tokens
    )
    return merged


def load_daily_deepseek(cost_dir: Path, days: int) -> Dict[str, UsageSnapshot]:
    """Load DeepSeek usage grouped by date."""
    from datetime import date, timedelta

    if not cost_dir.exists():
        return {}

    cutoff_date = date.today() - timedelta(days=days)
    daily: Dict[str, Dict[str, int]] = {}
    daily_cost: Dict[str, float] = {}

    for csv_file in sorted(cost_dir.rglob("amount-*.csv")):
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    try:
                        row_date = date.fromisoformat(row["utc_date"])
                    except (ValueError, KeyError):
                        continue
                    if row_date < cutoff_date:
                        continue
                    d = row["utc_date"]
                    if d not in daily:
                        daily[d] = {"input": 0, "output": 0, "cache_read": 0, "requests": 0}
                    token_type = row.get("type", "")
                    amount = int(row.get("amount", 0) or 0)
                    if token_type == "output_tokens":
                        daily[d]["output"] += amount
                    elif token_type == "input_cache_hit_tokens":
                        daily[d]["cache_read"] += amount
                    elif token_type == "input_cache_miss_tokens":
                        daily[d]["input"] += amount
                    elif token_type == "request_count":
                        daily[d]["requests"] += amount
        except (OSError, csv.Error):
            continue

    for csv_file in sorted(cost_dir.rglob("cost-*.csv")):
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    try:
                        row_date = date.fromisoformat(row["utc_date"])
                    except (ValueError, KeyError):
                        continue
                    if row_date < cutoff_date:
                        continue
                    d = row["utc_date"]
                    daily_cost[d] = daily_cost.get(d, 0) + float(row.get("cost", 0) or 0)
        except (OSError, csv.Error):
            continue

    result = {}
    for d, tokens in daily.items():
        result[d] = UsageSnapshot(
            input_tokens=tokens["input"],
            output_tokens=tokens["output"],
            cache_read_tokens=tokens["cache_read"],
            session_count=tokens["requests"],
            message_count=tokens["requests"],
            estimated_cost=daily_cost.get(d, 0),
            cost_currency="CNY",
            provider="deepseek",
            model="deepseek-v4-pro",
            models_used=["deepseek-v4-pro"],
            pricing_note="DeepSeek (平台实际费用)",
        )
    return result


def load_daily_claude(projects_dir: Path, days: int) -> Dict[str, UsageSnapshot]:
    """Load Claude Code usage grouped by date."""
    from datetime import date, timedelta

    if not projects_dir.exists():
        return {}

    cutoff = time.time() - (days * 86400)
    daily: Dict[str, Dict[str, Any]] = {}

    for jsonl_file in projects_dir.rglob("*.jsonl"):
        if "subagents" in jsonl_file.parts:
            continue
        if jsonl_file.stat().st_mtime < cutoff:
            continue

        try:
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    msg = entry.get("message", entry)
                    if msg.get("role") != "assistant" or not msg.get("usage"):
                        continue

                    # Get date from message timestamp
                    ts = msg.get("timestamp") or entry.get("timestamp")
                    if ts:
                        try:
                            d = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d")
                        except ValueError:
                            d = date.today().isoformat()
                    else:
                        d = date.today().isoformat()

                    if d not in daily:
                        daily[d] = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "count": 0, "models": {}}

                    u = msg["usage"]
                    daily[d]["input"] += u.get("input_tokens", 0)
                    daily[d]["output"] += u.get("output_tokens", 0)
                    daily[d]["cache_read"] += u.get("cache_read_input_tokens", 0)
                    daily[d]["cache_write"] += u.get("cache_creation_input_tokens", 0)
                    daily[d]["count"] += 1
                    model = msg.get("model", "unknown")
                    daily[d]["models"][model] = daily[d]["models"].get(model, 0) + 1
        except (OSError, UnicodeDecodeError):
            continue

    result = {}
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
    provider = "xiaomi" if "xiaomimimo" in base_url else "anthropic"

    for d, data in daily.items():
        primary = max(data["models"], key=data["models"].get) if data["models"] else "unknown"
        pricing = lookup_pricing(primary)
        cost = 0.0
        currency = "CNY"
        note = ""
        if pricing:
            cost = calculate_cost(pricing, data["input"], data["output"], data["cache_read"], data["cache_write"])
            currency = pricing["currency"]
            note = pricing.get("note", "")

        result[d] = UsageSnapshot(
            input_tokens=data["input"],
            output_tokens=data["output"],
            cache_read_tokens=data["cache_read"],
            cache_write_tokens=data["cache_write"],
            session_count=data["count"],
            message_count=data["count"],
            estimated_cost=cost,
            cost_currency=currency,
            provider=provider,
            model=primary,
            models_used=list(data["models"].keys()),
            pricing_note=note,
        )
    return result


def load_daily_usage(days: int, deepseek_dir: Optional[Path] = None) -> List[tuple]:
    """Load per-day usage from all sources. Returns sorted list of (date_str, UsageSnapshot)."""
    cc_daily = load_daily_claude(CLAUDE_HOME / "projects", days)
    ds_daily = load_daily_deepseek(deepseek_dir, days) if deepseek_dir else {}

    # Merge by date
    all_dates = sorted(set(cc_daily.keys()) | set(ds_daily.keys()))
    result = []
    for d in all_dates:
        cc = cc_daily.get(d)
        ds = ds_daily.get(d)
        if cc and ds:
            merged = merge_snapshots(cc, ds)
            merged.pricing_note = "MiMo + DeepSeek"
            result.append((d, merged))
        elif cc:
            result.append((d, cc))
        elif ds:
            result.append((d, ds))
    return result


def load_usage(days: int, deepseek_dir: Optional[Path] = None) -> UsageSnapshot:
    """Load and merge usage from all available sources."""
    # Source 1: Claude Code transcripts (MiMo via Xiaomi proxy)
    cc_snap = None
    hermes_snap = load_from_hermes(DB_PATH, days)
    if hermes_snap:
        cc_snap = hermes_snap
    else:
        cc_snap = load_from_claude_transcripts(CLAUDE_HOME / "projects", days)

    # Source 2: DeepSeek CSV exports
    ds_snap = None
    if deepseek_dir:
        ds_snap = load_from_deepseek_csvs(deepseek_dir, days)

    if cc_snap and ds_snap:
        merged = merge_snapshots(cc_snap, ds_snap)
        merged.pricing_note = "MiMo + DeepSeek"
        return merged
    if cc_snap:
        return cc_snap
    if ds_snap:
        return ds_snap

    print("No usage data found.", file=sys.stderr)
    return UsageSnapshot()


# ---------------------------------------------------------------------------
# Receipt rendering (token-receipt style)
# ---------------------------------------------------------------------------


def cjk_width(text: str) -> int:
    """Calculate display width treating CJK chars as 2 columns."""
    w = 0
    for ch in text:
        cp = ord(ch)
        if (0x4E00 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F or
            0xFF00 <= cp <= 0xFFEF or 0x3400 <= cp <= 0x4DBF or
            0x20000 <= cp <= 0x2A6DF or 0xF900 <= cp <= 0xFAFF or
            0x2E80 <= cp <= 0x2EFF or 0x31C0 <= cp <= 0x31EF or
            0xFE30 <= cp <= 0xFE4F):
            w += 2
        else:
            w += 1
    return w


def pad_line(text: str, width: int) -> str:
    """Pad a line to exact display width."""
    cur = cjk_width(text)
    return text + " " * max(0, width - cur)


def center_text(text: str, width: int) -> str:
    """Center text respecting CJK widths."""
    tw = cjk_width(text)
    pad = max(0, (width - tw) // 2)
    return " " * pad + text


def kv_line(label: str, value: str, width: int) -> str:
    """Format a key-value line with proper spacing."""
    lw = cjk_width(label)
    vw = cjk_width(value)
    spaces = max(1, width - lw - vw)
    return label + " " * spaces + value


def fmt_tokens(n: int) -> str:
    """Format token count with commas."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:,}"


def fmt_cost(amount: float, currency: str = "CNY") -> str:
    """Format cost with currency symbol."""
    symbol = "¥" if currency == "CNY" else "$" if currency == "USD" else f"{currency} "
    if amount == 0:
        return f"{symbol}0.00"
    if amount < 0.000001:
        return f"<{symbol}0.000001"
    if amount >= 1:
        return f"{symbol}{amount:.2f}"
    return f"{symbol}{amount:.4f}"


def receipt_id(snapshot: UsageSnapshot) -> str:
    """Generate a receipt ID like CC_20260503_A3F2B1."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    seed = f"{snapshot.provider}:{snapshot.model}:{snapshot.total_tokens}:{ts}"
    digest = hashlib.sha1(seed.encode()).hexdigest()[:6].upper()
    prov = snapshot.provider.lower()
    if "anthropic" in prov:
        prefix = "CC"
    elif "openai" in prov:
        prefix = "CX"
    elif "xiaomi" in prov or "mimo" in prov:
        prefix = "XM"
    elif "deepseek" in prov:
        prefix = "DS"
    else:
        prefix = "AI"
    return f"{prefix}_{ts}_{digest}"


def barcode(seed: str, width: int) -> str:
    """Generate a fake barcode from hash."""
    digest = hashlib.sha1(seed.encode()).hexdigest()
    patterns = ["|", "||", "| ", " ||", "|||", " |"]
    raw = "".join(patterns[int(c, 16) % len(patterns)] for c in digest)
    target = min(width - 8, max(24, width - 16))
    bar = raw[:target]
    pad = max(0, (width - len(bar)) // 2)
    return " " * pad + bar


def pick_footer(snapshot: UsageSnapshot, rid: str) -> str:
    """Pick a deterministic snarky footer."""
    key = f"{snapshot.provider}:{snapshot.model}:{snapshot.total_tokens}:{rid}"
    digest = int(hashlib.sha1(key.encode()).hexdigest()[:8], 16)
    return FOOTERS[digest % len(FOOTERS)]


def get_session_tip(projects_dir: Path) -> Optional[Dict[str, Any]]:
    """Get the latest usage from the current Claude Code session.

    Returns the most recent assistant message's usage data, which approximates
    the cost of the last API call (i.e., generating this receipt).
    """
    if not projects_dir.exists():
        return None

    # Find the most recently modified JSONL (current session)
    jsonl_files = [f for f in projects_dir.rglob("*.jsonl") if "subagents" not in f.parts]
    if not jsonl_files:
        return None

    latest_file = max(jsonl_files, key=lambda f: f.stat().st_mtime)

    last_usage = None
    last_model = None
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = entry.get("message", entry)
                if msg.get("role") == "assistant" and msg.get("usage"):
                    last_usage = msg["usage"]
                    last_model = msg.get("model", "")
    except (OSError, UnicodeDecodeError):
        return None

    if not last_usage:
        return None

    input_tok = last_usage.get("input_tokens", 0)
    output_tok = last_usage.get("output_tokens", 0)
    cache_read = last_usage.get("cache_read_input_tokens", 0)
    cache_write = last_usage.get("cache_creation_input_tokens", 0)
    total = input_tok + output_tok + cache_read + cache_write

    model = last_model or "mimo"
    pricing = lookup_pricing(model)
    cost = 0.0
    currency = "CNY"
    if pricing:
        cost = calculate_cost(pricing, input_tok, output_tok, cache_read, cache_write)
        currency = pricing["currency"]

    return {
        "input": input_tok,
        "output": output_tok,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "total": total,
        "cost": cost,
        "currency": currency,
        "model": model,
    }


def render_receipt(snapshot: UsageSnapshot, days: int, width: int = WIDTH, tip: Optional[Dict[str, Any]] = None) -> str:
    """Render the full receipt as ASCII art."""
    lines: List[str] = []

    def add(text: str = ""):
        lines.append(pad_line(text, width))

    def rule(char: str = "─"):
        add(char * width)

    def strong_rule():
        add("━" * width)

    # --- Logo ---
    add(center_text(" ▐▛███▜▌", width))
    add(center_text("▝▜█████▛▘", width))
    add(center_text("  ▘▘ ▝▝", width))
    add()
    add(center_text("HERMES", width))
    add()

    # --- Header ---
    add(center_text("感谢使用 Hermes Agent", width))
    rid = receipt_id(snapshot)
    add(center_text(f"小票号: {rid}", width))
    add(center_text(f"日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}", width))
    add()

    # --- Summary ---
    strong_rule()
    add(kv_line("统计周期", f"最近 {days} 天", width))
    add(kv_line("总会话数", str(snapshot.session_count), width))
    add(kv_line("总消息数", fmt_tokens(snapshot.message_count), width))
    if snapshot.api_calls:
        add(kv_line("API 调用", fmt_tokens(snapshot.api_calls), width))
    add()

    # --- Model breakdown ---
    rule()
    add(center_text("── 模型使用 ──", width))
    rule()
    if snapshot.models_used:
        for m in snapshot.models_used[:5]:
            name = m.split("/")[-1] if "/" in m else m
            if len(name) > 30:
                name = name[:27] + "..."
            add(f"  {name}")
    else:
        add(f"  {snapshot.model}")
    add()

    # --- Token breakdown ---
    strong_rule()
    add(kv_line("项目", "Tokens", width))
    strong_rule()

    add(kv_line("  输入 Tokens", fmt_tokens(snapshot.input_tokens), width))
    add(kv_line("  输出 Tokens", fmt_tokens(snapshot.output_tokens), width))
    if snapshot.cache_read_tokens:
        add(kv_line("  缓存读取", fmt_tokens(snapshot.cache_read_tokens), width))
    if snapshot.cache_write_tokens:
        add(kv_line("  缓存写入", fmt_tokens(snapshot.cache_write_tokens), width))
    if snapshot.reasoning_tokens:
        add(kv_line("  推理 Tokens", fmt_tokens(snapshot.reasoning_tokens), width))

    strong_rule()
    add(kv_line("总计", f"{fmt_tokens(snapshot.total_tokens)} Tokens", width))
    strong_rule()

    # --- Cost ---
    cost_label = f"{snapshot.cost_currency} 预估"
    add(kv_line(cost_label, fmt_cost(snapshot.estimated_cost, snapshot.cost_currency), width))
    if snapshot.pricing_note:
        add(kv_line("定价模型", snapshot.pricing_note, width))
    add(kv_line("供应商", snapshot.provider.upper(), width))

    # --- Tip (cost of generating this receipt) ---
    if tip and tip["total"] > 0:
        rule()
        add(center_text("── 小费 ──", width))
        rule()
        add(kv_line("  本次小票消耗", fmt_tokens(tip["total"]) + " Tokens", width))
        tip_label = f"  折合 {tip['currency']}"
        add(kv_line(tip_label, fmt_cost(tip["cost"], tip["currency"]), width))
        if snapshot.estimated_cost > 0:
            pct = tip["cost"] / snapshot.estimated_cost * 100
            add(kv_line("  占总费用", f"{pct:.1f}%", width))

    add()

    # --- Footer ---
    footer = pick_footer(snapshot, rid)
    add(center_text(footer, width))
    add()

    # --- Barcode ---
    add(barcode(rid, width))
    add(center_text(rid, width))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ESC/POS thermal printer output
# ---------------------------------------------------------------------------


def print_to_thermal(receipt_text: str, vid: int = 0x0456, pid: int = 0x0808):
    """Send receipt to a USB thermal printer via ESC/POS."""
    try:
        from escpos.printer import Usb
    except ImportError:
        print(
            "Error: python-escpos not installed.\n"
            "Install with: pip install python-escpos\n"
            "Then find your printer's VID/PID with: lsusb",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        p = Usb(vid, pid)
    except Exception as e:
        print(f"Cannot connect to printer (VID={vid:#06x} PID={pid:#06x}): {e}", file=sys.stderr)
        print("Find your printer with: lsusb  or  system_profiler SPUSBDataType", file=sys.stderr)
        sys.exit(1)

    p.set(align="center", bold=False, double_height=False, width=1, height=1)

    for line in receipt_text.split("\n"):
        # Thermal printers handle CJK via built-in fonts or driver
        p.text(line + "\n")

    p.text("\n\n")
    p.cut()
    p.close()
    print("Receipt sent to printer.")


# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------


def render_receipt_html(snapshot: UsageSnapshot, days: int, tip: Optional[Dict[str, Any]] = None, date_label: str = "") -> str:
    """Render a single receipt as a styled HTML card (token-receipt style)."""
    from html import escape

    rid = receipt_id(snapshot)
    footer = pick_footer(snapshot, rid)
    cost_fmt = fmt_cost(snapshot.estimated_cost, snapshot.cost_currency)

    # Token rows
    token_rows = ""
    token_rows += _html_row("输入 Tokens", fmt_tokens(snapshot.input_tokens))
    token_rows += _html_row("输出 Tokens", fmt_tokens(snapshot.output_tokens))
    if snapshot.cache_read_tokens:
        token_rows += _html_row("缓存读取", fmt_tokens(snapshot.cache_read_tokens))
    if snapshot.cache_write_tokens:
        token_rows += _html_row("缓存写入", fmt_tokens(snapshot.cache_write_tokens))
    if snapshot.reasoning_tokens:
        token_rows += _html_row("推理 Tokens", fmt_tokens(snapshot.reasoning_tokens))

    # Model list
    model_list = ""
    for m in (snapshot.models_used or [])[:5]:
        name = m.split("/")[-1] if "/" in m else m
        model_list += f'<div class="receipt-model">{escape(name)}</div>'

    # Tip section
    tip_html = ""
    if tip and tip["total"] > 0:
        tip_cost = fmt_cost(tip["cost"], tip["currency"])
        tip_html = f"""
    <div class="receipt-rule"></div>
    <div class="receipt-section-title">小费</div>
    <div class="receipt-rule"></div>
    {_html_row('本次小票消耗', fmt_tokens(tip['total']) + ' Tokens')}
    {_html_row('折合 ' + tip['currency'], tip_cost)}"""

    # Barcode
    bc = barcode(rid, 48)

    period_label = f"最近 {days} 天" if not date_label else date_label

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hermes Token Receipt — {escape(period_label)}</title>
<style>
:root {{
  color-scheme: light;
  --paper: #ffffff;
  --ink: #151515;
  --ink-secondary: #555;
  --rule: #232323;
  --receipt-width: 90mm;
  --pad-x: 7mm;
  --pad-top: 8mm;
  --pad-bottom: 6mm;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
  background: var(--paper);
  color: var(--ink);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Noto Sans Mono CJK SC", monospace;
}}
body {{
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0;
}}
.receipt-page {{
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}}
.receipt {{
  width: var(--receipt-width);
  background: var(--paper);
  padding: var(--pad-top) var(--pad-x) var(--pad-bottom);
  position: relative;
  overflow: hidden;
}}
.receipt-logo {{
  text-align: center;
  font-size: 4.2mm;
  line-height: 1.02;
  white-space: pre;
  margin-bottom: 1mm;
}}
.receipt-logo-svg {{
  text-align: center;
  margin-bottom: 1mm;
}}
.receipt-logo-svg svg {{
  display: inline-block;
}}
.receipt-logo-label {{
  text-align: center;
  font-size: 5mm;
  font-weight: bold;
  letter-spacing: 0.12em;
  margin-bottom: 4mm;
}}
.receipt-thanks, .receipt-meta {{
  text-align: center;
  font-size: 3.5mm;
  line-height: 1.4;
  color: var(--ink);
}}
.receipt-meta {{ color: var(--ink-secondary); }}
.receipt-rule {{
  border-top: 0.2mm solid var(--rule);
  margin: 3.5mm 0;
}}
.receipt-rule.strong {{
  border-top: 0.55mm solid var(--rule);
  margin: 3.5mm 0;
}}
.receipt-section-title {{
  text-align: center;
  font-size: 3.5mm;
  font-weight: bold;
  letter-spacing: 0.06em;
  margin: 1.5mm 0;
}}
.receipt-row {{
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 5mm;
  align-items: baseline;
  font-size: 3.6mm;
  line-height: 1.4;
  padding: 0.5mm 0;
}}
.receipt-label {{ color: var(--ink); }}
.receipt-value {{
  text-align: right;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}}
.receipt-total .receipt-label,
.receipt-total .receipt-value {{
  font-weight: bold;
  font-size: 3.8mm;
}}
.receipt-model {{
  font-size: 3.4mm;
  color: var(--ink-secondary);
  padding: 0.3mm 0;
}}
.receipt-footer {{
  margin-top: 4mm;
  text-align: center;
  font-size: 3.5mm;
  line-height: 1.4;
  color: var(--ink-secondary);
  font-style: italic;
}}
.receipt-barcode {{
  margin: 4mm 0 1.5mm;
  text-align: center;
  white-space: pre;
  font-size: 3.2mm;
  line-height: 1;
  letter-spacing: 0.5px;
  overflow: hidden;
}}
.receipt-barcode-id {{
  text-align: center;
  font-size: 3.2mm;
  color: var(--ink-secondary);
  word-break: break-all;
}}
.print-btn {{
  position: fixed;
  top: 16px;
  right: 16px;
  background: #1b1c1f;
  color: #fff;
  border: none;
  padding: 8px 20px;
  border-radius: 999px;
  font-size: 13px;
  cursor: pointer;
  font-family: inherit;
  z-index: 10;
}}
.print-btn:hover {{ background: #2d2d30; }}
@page {{ size: 80mm auto; margin: 0; }}
@media print {{
  body {{ background: #fff; padding: 0; print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
  .print-toolbar {{ display: none; }}
  .page-title {{ display: none; }}
  .receipt-page {{ gap: 0; }}
  .receipt {{ box-shadow: none; page-break-inside: avoid; margin: 0 auto; }}
}}
</style>
</head>
<body>
<button class="print-btn" onclick="window.print()">🖨️ 打印</button>
<div class="receipt-page">
<div class="receipt">
  <div class="receipt-logo"> ▐▛███▜▌
▝▜█████▛▘
  ▘▘ ▝▝</div>
  <div class="receipt-logo-label">HERMES</div>

  <div class="receipt-thanks">感谢使用 Hermes Agent</div>
  <div class="receipt-meta">小票号: {escape(rid)}</div>
  <div class="receipt-meta">日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>

  <div class="receipt-rule strong"></div>
  {_html_row('统计周期', escape(period_label))}
  {_html_row('总会话数', str(snapshot.session_count))}
  {_html_row('总消息数', fmt_tokens(snapshot.message_count))}

  <div class="receipt-rule"></div>
  <div class="receipt-section-title">模型使用</div>
  <div class="receipt-rule"></div>
  {model_list}

  <div class="receipt-rule strong"></div>
  <div class="receipt-row">
    <span class="receipt-label">项目</span>
    <span class="receipt-value">Tokens</span>
  </div>
  <div class="receipt-rule strong"></div>
  {token_rows}
  <div class="receipt-rule strong"></div>
  {_html_row('总计', fmt_tokens(snapshot.total_tokens) + ' Tokens', total=True)}
  <div class="receipt-rule strong"></div>

  {_html_row(snapshot.cost_currency + ' 预估', cost_fmt)}
  {('<div class="receipt-row"><span class="receipt-label">定价模型</span><span class="receipt-value">' + escape(snapshot.pricing_note) + '</span></div>') if snapshot.pricing_note else ''}
  {_html_row('供应商', snapshot.provider.upper())}
  {tip_html}

  <div class="receipt-rule strong"></div>
  <div class="receipt-footer">{escape(footer)}</div>
  <div class="receipt-barcode">{escape(bc)}</div>
  <div class="receipt-barcode-id">{escape(rid)}</div>
</div>
</div>
</body>
</html>"""


def _html_row(label: str, value: str, total: bool = False) -> str:
    from html import escape
    cls = 'receipt-row receipt-total' if total else 'receipt-row'
    return f'<div class="{cls}"><span class="receipt-label">{escape(label)}</span><span class="receipt-value">{escape(value)}</span></div>'


def _combine_daily_html(receipts: List[str], daily: List[tuple]) -> str:
    """Combine multiple daily receipt HTMLs into one multi-page file."""
    from html import escape
    total_cost = sum(snap.estimated_cost for _, snap in daily)
    total_tokens = sum(snap.total_tokens for _, snap in daily)

    # Extract just the <body> content from each receipt
    bodies = []
    for html_str in receipts:
        start = html_str.find('<div class="receipt">')
        end = html_str.find('</body>')
        if start != -1 and end != -1:
            bodies.append(html_str[start:end].replace('<div class="receipt">', '<div class="receipt receipt-page-item">', 1))

    body_content = "\n<hr class='page-break'>\n".join(bodies)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hermes Token Receipt — 最近 {len(daily)} 天</title>
<style>
{receipts[0][receipts[0].find('<style>')+7:receipts[0].find('</style>')]}
.page-break {{
  border: none;
  margin: 0;
  padding: 0;
  page-break-after: always;
}}
.summary-bar {{
  background: rgba(255,255,255,0.08);
  color: #eee;
  padding: 12px 24px;
  border-radius: 8px;
  text-align: center;
  font-size: 14px;
  margin-bottom: 16px;
}}
.summary-bar strong {{ color: #e94560; }}
@media print {{
  .print-toolbar {{ display: none; }}
  .summary-bar {{ display: none; }}
  .page-break {{ page-break-after: always; }}
}}
</style>
</head>
<body>
<div class="print-toolbar">
  <button class="print-btn" onclick="window.print()">🖨️ 打印全部小票 ({len(daily)} 天)</button>
</div>
<div class="summary-bar">
  最近 {len(daily)} 天 · 总计 <strong>{fmt_tokens(total_tokens)} Tokens</strong> · <strong>{fmt_cost(total_cost, 'CNY')}</strong>
</div>
<div class="receipt-page">
{body_content}
</div>
</body>
</html>"""


def render_html(receipt_text: str) -> str:
    """Wrap plain receipt text in a printable HTML page (legacy fallback)."""
    from html import escape
    escaped = escape(receipt_text)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Hermes Token Receipt</title>
<style>
body {{ display: flex; justify-content: center; padding: 40px; background: #f5f5f5; }}
.receipt {{ background: white; padding: 24px 32px; font-family: 'Courier New', monospace;
  font-size: 13px; line-height: 1.4; white-space: pre; max-width: 400px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1); }}
@media print {{ body {{ background: white; padding: 0; }} .receipt {{ box-shadow: none; }} }}
</style>
</head>
<body><div class="receipt">{escaped}</div></body>
</html>"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Hermes Token Receipt Printer")
    parser.add_argument("--days", type=int, default=1, help="Days to aggregate (default: 1)")
    parser.add_argument("--width", type=int, default=WIDTH, help=f"Receipt width in chars (default: {WIDTH})")
    parser.add_argument("--printer", action="store_true", help="Send to ESC/POS thermal printer")
    parser.add_argument("--vid", type=lambda x: int(x, 0), default=0x0456, help="USB Vendor ID (hex)")
    parser.add_argument("--pid", type=lambda x: int(x, 0), default=0x0808, help="USB Product ID (hex)")
    parser.add_argument("--html", type=str, metavar="FILE", help="Export as printable HTML")
    parser.add_argument("--html-dir", type=str, metavar="DIR", help="Export one HTML file per day to directory")
    parser.add_argument("--tip", action="store_true", default=True, help="Show cost of generating this receipt (default: on)")
    parser.add_argument("--no-tip", action="store_true", help="Hide the tip section")
    parser.add_argument("--per-day", action="store_true", help="Generate individual receipts per day instead of aggregated")
    parser.add_argument("--deepseek-dir", type=str, default=None, help="Path to DeepSeek usage CSV directory")
    parser.add_argument("--db", type=str, default=str(DB_PATH), help="Path to Hermes state.db")
    args = parser.parse_args()

    ds_dir = Path(args.deepseek_dir) if args.deepseek_dir else None
    tip = get_session_tip(CLAUDE_HOME / "projects") if not args.no_tip else None

    if args.per_day:
        # Per-day mode: generate individual receipts
        daily = load_daily_usage(args.days, ds_dir)
        if not daily:
            print("No usage data found.", file=sys.stderr)
            sys.exit(1)

        if args.html_dir:
            # Individual HTML per day
            out_dir = Path(args.html_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            for d, snap in daily:
                html = render_receipt_html(snap, 1, tip=tip, date_label=d)
                p = out_dir / f"receipt-{d}.html"
                p.write_text(html, encoding="utf-8")
                print(f"  {d} -> {p.name}")
            print(f"\nDone! {len(daily)} files in {out_dir}/")
        elif args.html:
            # Multi-page HTML with one receipt per day
            all_html = []
            for d, snap in daily:
                all_html.append(render_receipt_html(snap, 1, tip=tip, date_label=d))
            combined = _combine_daily_html(all_html, daily)
            Path(args.html).write_text(combined, encoding="utf-8")
            print(f"HTML receipts saved to {args.html} ({len(daily)} days)")
        else:
            # Terminal: print each day's receipt
            for d, snap in daily:
                receipt = render_receipt(snap, 1, args.width, tip=tip)
                print(f"\n{'='*args.width}")
                print(f"  {d}")
                print(f"{'='*args.width}\n")
                print(receipt)
    else:
        # Aggregated mode (original behavior)
        snapshot = load_usage(args.days, ds_dir)
        if args.html:
            html = render_receipt_html(snapshot, args.days, tip=tip)
            Path(args.html).write_text(html, encoding="utf-8")
            print(f"HTML receipt saved to {args.html}")
        elif args.printer:
            receipt = render_receipt(snapshot, args.days, args.width, tip=tip)
            print_to_thermal(receipt, args.vid, args.pid)
        else:
            receipt = render_receipt(snapshot, args.days, args.width, tip=tip)
            print(receipt)


if __name__ == "__main__":
    main()
