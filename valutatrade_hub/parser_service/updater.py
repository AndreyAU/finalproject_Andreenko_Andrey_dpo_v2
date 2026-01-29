import logging
from datetime import datetime

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import BaseApiClient


logger = logging.getLogger("valutatrade")


class RatesUpdater:
    """
    Координатор обновления курсов валют.

    Отвечает за:
    - вызов всех API-клиентов
    - объединение полученных курсов
    - передачу данных в storage
    - логирование процесса

    Не содержит бизнес-логики (TTL, reverse-rate и т.п.).
    """

    def __init__(self, clients: list[BaseApiClient], storage) -> None:
        self.clients = clients
        self.storage = storage

    def run_update(self) -> int:
        logger.info("Starting rates update")

        all_rates: dict[str, float] = {}
        updated_sources: list[str] = []

        for client in self.clients:
            client_name = client.__class__.__name__

            try:
                rates = client.fetch_rates()

                if not rates:
                    logger.warning(
                        f"{client_name}: no rates returned"
                    )
                    continue

                all_rates.update(rates)
                updated_sources.append(client_name)

                logger.info(
                    f"{client_name}: fetched {len(rates)} rates"
                )

            except ApiRequestError as e:
                logger.error(
                    f"{client_name}: failed to fetch rates: {e}"
                )
                continue

            except Exception as e:
                # защита от неожиданных ошибок
                logger.exception(
                    f"{client_name}: unexpected error: {e}"
                )
                continue

        if not all_rates:
            logger.warning("No rates collected from any source")
            return 0

        # фиксируем момент обновления
        refreshed_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        self.storage.save_snapshot(
            rates=all_rates,
            updated_at=refreshed_at,
        )

        logger.info(
            f"Rates update finished: {len(all_rates)} pairs, "
            f"sources={updated_sources}"
        )

        return len(all_rates)

