# logger_config.py

import logging
import os

def setup_logger(name: str, log_file: str = "logs/app.log", level: int = logging.INFO) -> logging.Logger:
    # Garante que a pasta de logs exista
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Cria o formatador (como a mensagem será exibida)
    formatter = logging.Formatter(
        fmt='[%(levelname)s] [%(name)s] %(message)s'
    )

    # Cria handler para salvar log em arquivo
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Cria handler para exibir log no terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Cria ou recupera o logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evita múltiplos handlers (se já estiverem adicionados)
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    logger.propagate = False  # Evita duplicação de mensagens em libs que também usam logging
    return logger
