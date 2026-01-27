import logging
from functools import wraps
from datetime import datetime
from typing import Callable, Optional


def log_action(action: str, verbose: bool = False):
    """
    Декоратор для логирования доменных операций.

    Логирует (INFO):
    - timestamp (ISO)
    - action (BUY / SELL / REGISTER / LOGIN)
    - user_id или username
    - currency, amount
    - rate, base (если применимо)
    - result (OK / ERROR)
    - error_type / error_message (при ошибке)

    Требования:
    - не глотает исключения
    - поддерживает verbose-контекст (before -> after)
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("valutatrade")
            timestamp = datetime.now().isoformat(timespec="seconds")

            def extract_context(result: Optional[dict]) -> dict:
                if not isinstance(result, dict):
                    return {}

                ctx = {
                    "user": (
                        result.get("username")
                        or result.get("user_id")
                        or kwargs.get("user_id")
                        or "unknown"
                    ),
                    "currency": result.get("currency"),
                    "amount": result.get("amount"),
                    "rate": result.get("rate"),
                    "base": result.get("base"),
                }

                if verbose:
                    ctx["before"] = result.get("before")
                    ctx["after"] = result.get("after")

                return ctx

            try:
                result = func(*args, **kwargs)
                ctx = extract_context(result)

                logger.info(
                    "%s %s user=%s currency=%s amount=%s rate=%s base=%s result=OK",
                    timestamp,
                    action,
                    ctx["user"],
                    ctx.get("currency"),
                    ctx.get("amount"),
                    ctx.get("rate"),
                    ctx.get("base"),
                )

                if verbose and ctx.get("before") is not None:
                    logger.debug(
                        "%s %s wallet_before=%s wallet_after=%s",
                        timestamp,
                        action,
                        ctx.get("before"),
                        ctx.get("after"),
                    )

                return result

            except Exception as exc:
                logger.error(
                    "%s %s result=ERROR error_type=%s error_message=%s",
                    timestamp,
                    action,
                    type(exc).__name__,
                    str(exc),
                )
                raise

        return wrapper

    return decorator

