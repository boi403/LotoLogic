"""
Cache local de concursos da Caixa.

Estratégia:
- Cada loteria vira um arquivo JSON em `~/.lotologic-core/cache/{game}.json`
- Cada arquivo contém {"draws": [...], "last_synced": "ISO date"}
- Sync incremental: baixa só os concursos posteriores ao último em cache
- Funciona offline depois do primeiro sync

Por que JSON e não SQLite? Porque o app LotoLogic original usa SQL (Postgres),
mas para um cache simples de algumas centenas de concursos, JSON é suficiente,
zero-deps e fácil de inspecionar manualmente.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from ..domain.lottery import Draw, GameSpec, get_spec
from .caixa_api import CaixaApiClient, CaixaApiError


def get_cache_dir() -> Path:
    """Diretório de cache (cross-platform)."""
    # Permite override via env var
    if "LOTOLOGIC_CACHE_DIR" in os.environ:
        return Path(os.environ["LOTOLOGIC_CACHE_DIR"])
    return Path.home() / ".lotologic-core" / "cache"


def _cache_path(game: str) -> Path:
    return get_cache_dir() / f"{game}.json"


def _draw_to_dict(d: Draw) -> dict:
    out = asdict(d)
    if d.draw_date is not None:
        out["draw_date"] = d.draw_date.isoformat()
    out["numbers"] = list(d.numbers)
    return out


def _dict_to_draw(d: dict) -> Draw:
    raw_date = d.get("draw_date")
    parsed_date: Optional[date] = None
    if raw_date:
        parsed_date = date.fromisoformat(raw_date)
    return Draw(
        contest=d["contest"],
        game=d["game"],
        numbers=tuple(d["numbers"]),
        draw_date=parsed_date,
        accumulated=d.get("accumulated", False),
    )


def load_cache(game: str) -> list[Draw]:
    """Carrega concursos cacheados para uma loteria. Lista vazia se não há cache."""
    path = _cache_path(game)
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [_dict_to_draw(d) for d in raw.get("draws", [])]


def save_cache(game: str, draws: list[Draw]) -> None:
    """Persiste concursos no cache, ordenados por concurso."""
    path = _cache_path(game)
    path.parent.mkdir(parents=True, exist_ok=True)
    sorted_draws = sorted(draws, key=lambda d: d.contest)
    payload = {
        "game": game,
        "last_synced": datetime.now().isoformat(timespec="seconds"),
        "n_draws": len(sorted_draws),
        "draws": [_draw_to_dict(d) for d in sorted_draws],
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def sync_game(
    game: str,
    client: Optional[CaixaApiClient] = None,
    full_resync: bool = False,
    progress_cb=None,
) -> tuple[int, int]:
    """
    Sincroniza o cache local com a API. Retorna (n_total_apos, n_baixados_agora).

    Estratégia incremental:
        1. Carrega cache existente.
        2. Pergunta à API qual é o concurso mais recente (latest).
        3. Se o cache está desatualizado, baixa só os faltantes.
        4. `full_resync=True` ignora o cache e baixa tudo de novo.

    O parâmetro `progress_cb(contest, target)` é chamado a cada concurso baixado,
    para o CLI imprimir uma barra de progresso.
    """
    spec: GameSpec = get_spec(game)  # valida a loteria
    client = client or CaixaApiClient()

    cached = [] if full_resync else load_cache(game)
    cached_by_contest = {d.contest: d for d in cached}
    last_cached = max(cached_by_contest) if cached_by_contest else 0

    # 1. Descobre o concurso mais recente
    latest = client.fetch_latest(game)
    target_contest = latest.contest

    if target_contest <= last_cached:
        # cache já está atualizado
        return len(cached), 0

    # 2. Baixa os faltantes (last_cached+1 até target_contest)
    new_draws: list[Draw] = []
    start = max(last_cached + 1, 1)
    for contest in range(start, target_contest + 1):
        if progress_cb:
            progress_cb(contest, target_contest)
        try:
            d = client.fetch_contest(game, contest)
            new_draws.append(d)
        except CaixaApiError:
            # alguns concursos antigos podem não estar disponíveis; pula
            continue

    # 3. Mescla e salva
    merged = list(cached_by_contest.values()) + new_draws
    save_cache(game, merged)
    return len(merged), len(new_draws)


def cache_summary() -> dict[str, dict]:
    """Resumo do estado do cache de todas as loterias."""
    out = {}
    cache_dir = get_cache_dir()
    if not cache_dir.exists():
        return out
    for jsonfile in cache_dir.glob("*.json"):
        try:
            payload = json.loads(jsonfile.read_text(encoding="utf-8"))
            out[jsonfile.stem] = {
                "n_draws": payload.get("n_draws", 0),
                "last_synced": payload.get("last_synced"),
                "first_contest": (
                    payload["draws"][0]["contest"] if payload.get("draws") else None
                ),
                "last_contest": (
                    payload["draws"][-1]["contest"] if payload.get("draws") else None
                ),
            }
        except (json.JSONDecodeError, KeyError, IndexError):
            continue
    return out
