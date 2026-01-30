# valutatrade_hub/parser_service/updater.py
import logging
from datetime import datetime

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import BaseApiClient


logger = logging.getLogger("valutatrade")


class RatesUpdater:
    def __init__(self, clients: list[BaseApiClient], storage) -> None:
        self.clients = clients
        self.storage = storage

    def run_update(self) -> dict:
        logger.info("Starting rates update")

        all_rates: dict[str, float] = {}
        sources_ok: list[str] = []
        errors: list[str] = []

        for client in self.clients:
            name = client.__class__.__name__

            try:
                rates = client.fetch_rates()
                if not rates:
                    logger.warning(f"{name}: no rates returned")
                    continue

                all_rates.update(rates)
                sources_ok.append(name)

                logger.info(f"{name}: fetched {len(rates)} rates")

            except ApiRequestError as e:
                msg = f"{name}: {e}"
                errors.append(msg)
                logger.error(msg)

            except Exception as e:
                msg = f"{name}: unexpected error: {e}"
                errors.append(msg)
                logger.exception(msg)

        if not all_rates:
            logger.warning("No rates collected from any source")
            return {
                "count": 0,
                "last_refresh": None,
                "sources": sources_ok,
                "errors": errors,
            }

        refreshed_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        self.storage.save_snapshot(
            rates=all_rates,
            updated_at=refreshed_at,
        )

        logger.info(
            f"Rates update finished: {len(all_rates)} pairs, sources={sources_ok}"
        )

        return {
            "count": len(all_rates),
            "last_refresh": refreshed_at,
            "sources": sources_ok,
            "errors": errors,
        }

