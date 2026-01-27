import logging
from functools import wraps
from datetime import datetime


def log_action(action: str, verbose: bool = False):
    """
    Декоратор для логирования доменных операций (BUY, SELL, LOGIN, REGISTER).

    - не глотает исключения
    - логирует SUCCESS / ERROR
    - формат человекочитаемый
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("valutatrade")

            timestamp = datetime.now().isoformat(timespec="seconds")

            try:
                result = func(*args, **kwargs)

                logger.info(
                    "%s %s result=OK args=%s kwargs=%s",
                    timestamp,
                    action,
                    args,
                    kwargs,
                )

                if verbose:
                    logger.debug(
                        "%s %s result=%s",
                        timestamp,
                        action,
                        result,
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

