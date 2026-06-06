"""
Claude Proxy Bridge for the CAPTCHA System
═══════════════════════════════════════════════════════════════════════════════
Routes all captcha workflow HTTP calls through the antigravity-claude-proxy
at http://localhost:8080 instead of OpenRouter.ai, when the proxy is running
and no OpenRouter key is available (or when the GUI toggle is ON).

HOW IT WORKS
────────────
Every workflow solver (MathCaptchaSolver, SixCharAlphanumSolver, …) posts to:

    POST {OPENROUTER_API_ENDPOINT}
    Authorization: Bearer {OPENROUTER_API_KEY}
    Body: {"model": AI_VISION_MODEL, "messages": [...]}

The Claude proxy listens on its `/v1/chat/completions` endpoint and accepts the
exact same OpenAI-compatible request body, so the ONLY thing that changes is:

    OPENROUTER_API_ENDPOINT  →  http://localhost:8080/v1/chat/completions
    AI_VISION_MODEL          →  gemini-3-flash  (or any proxy model)
    OPENROUTER_API_KEY       →  "test"           (proxy ignores auth)

USAGE
─────
    from ai_captcha.claude_proxy_bridge import build_proxy_config, is_proxy_healthy

    if is_proxy_healthy():
        cfg = build_proxy_config()          # pass to any Solver or Dispatcher
    else:
        cfg = None                          # fall back to normal OpenRouter path
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ── Proxy defaults (match discovery_manager.py constants) ────────────────────
_PROXY_DEFAULT_URL   = os.getenv("ANTHROPIC_BASE_URL",  "http://localhost:8080")
_PROXY_DEFAULT_MODEL = os.getenv("CLAUDE_PROXY_MODEL",  "gemini-3-flash")
_PROXY_DEFAULT_TOKEN = os.getenv("ANTHROPIC_AUTH_TOKEN", "test")

# OpenAI-compatible chat completions endpoint exposed by the proxy
_PROXY_CHAT_ENDPOINT = f"{_PROXY_DEFAULT_URL.rstrip('/')}/v1/chat/completions"


def is_proxy_healthy(timeout: float = 3.0) -> bool:
    """Return True if the claude proxy health endpoint responds 200 OK."""
    import httpx  # already present in discovery_squad venv; fall back to requests
    health_url = f"{_PROXY_DEFAULT_URL.rstrip('/')}/health"
    try:
        resp = httpx.get(health_url, timeout=timeout)
        return resp.status_code == 200
    except Exception:
        try:
            import requests as _req
            resp = _req.get(health_url, timeout=timeout)
            return resp.status_code == 200
        except Exception:
            return False


def build_proxy_config(
    model:       Optional[str] = None,
    base_url:    Optional[str] = None,
    auth_token:  Optional[str] = None,
    extra:       Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a solver config dict that points every workflow at the Claude proxy
    instead of OpenRouter.

    The returned dict is a drop-in replacement for the normal captcha_config
    dict consumed by every Solver (__init__ accepts a `config` kwarg).

    Args:
        model      : Override the proxy model (default: CLAUDE_PROXY_MODEL env
                     or "gemini-3-flash").
        base_url   : Override the proxy base URL (default: ANTHROPIC_BASE_URL
                     env or "http://localhost:8080").
        auth_token : Override the bearer token (default: "test").
        extra      : Additional keys to merge into the returned config dict.

    Returns:
        Dict suitable for passing as `config=` to CaptchaDispatcher or any
        individual Solver class.
    """
    resolved_model    = model      or _PROXY_DEFAULT_MODEL
    resolved_base_url = base_url   or _PROXY_DEFAULT_URL
    resolved_token    = auth_token or _PROXY_DEFAULT_TOKEN
    endpoint          = f"{resolved_base_url.rstrip('/')}/v1/chat/completions"

    cfg: Dict[str, Any] = {
        # ── Identity ──────────────────────────────────────────────────────────
        "OPENROUTER_API_KEY":      resolved_token,   # proxy ignores auth

        # ── Routing ──────────────────────────────────────────────────────────
        "OPENROUTER_API_ENDPOINT": endpoint,         # points at localhost proxy
        "AI_VISION_MODEL":         resolved_model,
        "AI_AUDIO_MODEL":          resolved_model,   # proxy handles audio too

        # ── Timing ────────────────────────────────────────────────────────────
        "OPENROUTER_TIMEOUT":      60,               # proxy may take slightly longer
        "RETRY_DELAY":             3.0,              # conservative retry spacing

        # ── Caching ───────────────────────────────────────────────────────────
        "ENABLE_CACHING":          True,
        "CACHE_TTL":               3600,

        # ── Source tag (informational) ────────────────────────────────────────
        "_via_claude_proxy":       True,
    }

    if extra:
        cfg.update(extra)

    logger.info(
        "[CaptchaProxyBridge] Config built → endpoint=%s  model=%s",
        endpoint, resolved_model,
    )
    return cfg


def get_proxy_config_if_available(
    openrouter_keys: Optional[list] = None,
    force_proxy:      bool           = False,
) -> Optional[Dict[str, Any]]:
    """
    Decide whether to use the proxy config or fall back to OpenRouter.

    Decision logic:
      1. force_proxy=True  → always use proxy (GUI toggle is ON)
      2. No valid OpenRouter keys  → try proxy automatically
      3. Valid OpenRouter keys present  → return None (use normal path)

    Returns:
        A proxy config dict if the proxy should be used, or None to use
        the normal OpenRouter path.
    """
    has_or_keys = bool(
        openrouter_keys and any(k.strip() for k in openrouter_keys)
    )

    if force_proxy or not has_or_keys:
        if is_proxy_healthy():
            logger.info("[CaptchaProxyBridge] ✓ Proxy healthy — captcha will use claude proxy.")
            return build_proxy_config()
        else:
            if force_proxy:
                logger.error(
                    "[CaptchaProxyBridge] ✗ Proxy forced but NOT reachable at %s. "
                    "Captcha solving may fail.",
                    _PROXY_DEFAULT_URL,
                )
            else:
                logger.warning(
                    "[CaptchaProxyBridge] No OpenRouter keys and proxy not reachable — "
                    "captcha solving will likely fail."
                )
            return None

    # Normal OpenRouter path
    return None
