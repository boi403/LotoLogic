"""
Cliente HTTP da API pública de loterias da CAIXA.

Usa a mesma fonte que o workflow `update-data.yml` do LotoLogic
(loteriascaixa-api.herokuapp.com) e que o projeto guto-alves/loterias-api
expõe via REST. Camada fina — sem cache nem retry sofisticado, isso
é responsabilidade da camada de uso.

Por que não usar a API Java do guto-alves diretamente? Porque não tem
deploy público estável; o herokuapp.com sim. Mas o contrato é compatível.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from typing import Any, Iterator, Optional

from ..domain.lottery import Draw, get_spec

DEFAULT_BASE_URL = "https://loteriascaixa-api.herokuapp.com/api"
DEFAULT_TIMEOUT = 30
DEFAULT_USER_AGENT = "lotologic-core/1.0"


class CaixaApiError(RuntimeError):
    """Erro de comunicação com a API da Caixa."""


def _http_get_json(url: str, timeout: int = DEFAULT_TIMEOUT) -> Any:
    """GET simples com decoding JSON. Sem dependências externas."""
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise CaixaApiError(f"HTTP {e.code} em {url}") from e
    except urllib.error.URLError as e:
        raise CaixaApiError(f"Falha de rede em {url}: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise CaixaApiError(f"Resposta não-JSON em {url}") from e


def _parse_caixa_date(s: Optional[str]) -> Optional[date]:
    """A API devolve datas em DD/MM/YYYY ou ISO. Tolerante a ambos."""
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _payload_to_draw(game: str, payload: dict) -> Draw:
    """Converte payload bruto da API em entidade Draw.

    Casos especiais:

    - **Super Sete**: a API retorna 7 dígitos (0-9), um por coluna, podendo
      repetir entre colunas. Usamos encoding virtual `coluna*10 + dígito`
      (col 1 → 0..9, col 2 → 10..19, ..., col 7 → 60..69) para caber no
      modelo geral de "tupla de inteiros únicos". Isso bate com o universe=70
      definido em domain/lottery.py.

    - **Dupla Sena**: cada concurso tem 2 sorteios independentes ('1' e '2').
      A API retorna 12 dezenas (6+6) concatenadas. Usamos só o primeiro
      sorteio (mais comum em análises) — o segundo é equivalente
      estatisticamente para frequência/atraso de longo prazo.
    """
    spec = get_spec(game)
    raw_numbers = payload.get("dezenas") or payload.get("dezenasOrdemSorteio") or []

    # Super Sete: encoding virtual coluna*10 + dígito
    if game == "supersete":
        digits = [int(n) for n in raw_numbers]
        if len(digits) != spec.draw_size:
            raise CaixaApiError(
                f"{game}#{payload.get('concurso')}: "
                f"esperava {spec.draw_size} dígitos, recebi {len(digits)}"
            )
        numbers = tuple(col * 10 + dig for col, dig in enumerate(digits))
    # Dupla Sena: pega só o 1º sorteio (primeiras 6 dezenas)
    elif game == "duplasena" and len(raw_numbers) == spec.draw_size * 2:
        numbers = tuple(int(n) for n in raw_numbers[: spec.draw_size])
    else:
        numbers = tuple(int(n) for n in raw_numbers)
        if len(numbers) != spec.draw_size:
            raise CaixaApiError(
                f"{game}#{payload.get('concurso')}: "
                f"esperava {spec.draw_size} dezenas, recebi {len(numbers)}"
            )

    return Draw(
        contest=int(payload["concurso"]),
        game=game,
        numbers=numbers,
        draw_date=_parse_caixa_date(payload.get("data")),
        accumulated=bool(payload.get("acumulou", False)),
    )


class CaixaApiClient:
    """
    Cliente leve da API pública.

    Uso:
        client = CaixaApiClient()
        latest = client.fetch_latest("megasena")
        for draw in client.iter_history("lotofacil", since=2900):
            ...

    O método `iter_history` faz throttling automático (200ms entre requests,
    igual o workflow oficial) para não estourar o servidor — compatível com
    a regra do LotoLogic.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        request_delay_ms: int = 200,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.request_delay_s = request_delay_ms / 1000.0
        self.timeout = timeout

    def fetch_latest(self, game: str) -> Draw:
        spec = get_spec(game)  # valida que a loteria existe
        url = f"{self.base_url}/{spec.key}/latest"
        return _payload_to_draw(spec.key, _http_get_json(url, self.timeout))

    def fetch_contest(self, game: str, contest: int) -> Draw:
        spec = get_spec(game)
        url = f"{self.base_url}/{spec.key}/{contest}"
        return _payload_to_draw(spec.key, _http_get_json(url, self.timeout))

    def iter_history(
        self,
        game: str,
        since: int = 1,
        until: Optional[int] = None,
    ) -> Iterator[Draw]:
        """
        Itera concursos do `since` ao `until` (inclusive).

        Se `until` for None, descobre o último via /latest. Útil para
        sincronização incremental — mesma lógica do workflow PHP do
        LotoLogic, só que reusável em qualquer contexto.
        """
        if until is None:
            until = self.fetch_latest(game).contest

        for n in range(since, until + 1):
            try:
                yield self.fetch_contest(game, n)
            except CaixaApiError:
                # Concursos antigos podem ter falhas pontuais — não
                # interromper a iteração. O usuário decide o que fazer.
                continue
            time.sleep(self.request_delay_s)
