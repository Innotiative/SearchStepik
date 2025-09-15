from pydantic_settings import BaseSettings
import logging
import os


class Settings(BaseSettings):
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    embedding_model: str = "cointegrated/LaBSE-en-ru" #  we also suggest try "cai-forever/ru-en-RoSBERTa"
    load_courses: bool = True


settings = Settings()


def setup_logging():
    log_path = "app/log.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # Создаём файл, если его нет (без записи)
    if not os.path.exists(log_path):
        with open(log_path, "a"):
            pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode='a'),
            logging.StreamHandler()
        ]
    )

    # Отключаем логи от httpx
    logging.getLogger("httpx").setLevel(logging.WARNING)
