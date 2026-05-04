"""
Cursor Opus 间接接口 — 通过 Cursor 的本地代理调用 Claude Opus。

Cursor IDE 内置了 Claude Opus 的访问能力，但不暴露直接 API。
本模块通过 Cursor 的本地代理端口（默认 4567）提供 OpenAI 兼容接口，
使治理框架的三省可以使用 Opus 进行高推理任务。

使用方式：
1. 启动 Cursor IDE（确保 Cursor 使用了 Opus 模型）
2. 代理自动监听 localhost:4567
3. 三省 agent 通过此接口调用 Opus
"""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CursorOpusProxy:
    """
    通过 Cursor 本地代理调用 Claude Opus。

    工作原理：
    - Cursor IDE 在运行时会启动一个本地 HTTP 代理
    - 此代理接受 OpenAI 兼容格式的请求
    - 内部转发给 Cursor 的 Claude Opus 访问权限
    - 本类将此接口封装为 Hermes transport 可用的格式
    """

    def __init__(
        self,
        base_url: str = "http://localhost:4567/v1",
        api_key: str = "cursor-proxy",
        model: str = "claude-opus-4-7",
        timeout: int = 300,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    @property
    def is_available(self) -> bool:
        """Check if Cursor proxy is reachable."""
        import urllib.request
        try:
            req = urllib.request.Request(
                f"{self._base_url}/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def chat_completion(
        self,
        messages: list,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request through Cursor's proxy.
        Returns OpenAI-compatible response dict.
        """
        import urllib.request

        payload = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"Cursor proxy request failed: {e}")
            raise

    def get_model_config(self) -> Dict[str, Any]:
        """
        Return model config dict suitable for AIAgent constructor.
        Uses base_url + api_key to route through Cursor proxy.
        """
        return {
            "base_url": self._base_url,
            "api_key": self._api_key,
            "model": self._model,
        }


def get_cursor_proxy_config(config: dict) -> Optional[Dict[str, Any]]:
    """
    Extract Cursor proxy config from governance config.
    Returns model config dict or None if not available.
    """
    proxy_cfg = config.get("cursor_proxy", {})
    if not proxy_cfg.get("enabled", False):
        return None

    proxy = CursorOpusProxy(
        base_url=proxy_cfg.get("base_url", "http://localhost:4567/v1"),
        api_key=proxy_cfg.get("api_key", "cursor-proxy"),
        model=proxy_cfg.get("model", "claude-opus-4-7"),
    )

    if not proxy.is_available:
        logger.warning("Cursor proxy not available, skipping Opus model")
        return None

    return proxy.get_model_config()
