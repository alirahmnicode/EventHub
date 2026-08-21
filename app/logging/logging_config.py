import logging

from app.middleware.request_id import get_request_id


class RequestIDLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def configure_logging():
    handler = logging.StreamHandler()
    handler.addFilter(RequestIDLogFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"
        )
    )
    logging.basicConfig(level=logging.INFO, handlers=[handler])
