import json
import re

import pandas as pd


from config.config import *
from utils.logger import *

logger = setup_logger(__name__)


class TextCleaner:
    @staticmethod
    def clean_text(texto):
        """
        Limpa texto de campos multilinha para melhorar embedding.
        """
        if not texto:
            return texto

        texto = re.sub(r'(?i)Projeto Pedagógico do Curso.*?\n', '', texto)
        texto = re.sub(r'(?i)Tecnologia em .*?\n', '', texto)
        texto = re.sub(r'\n\s*\d+\s*\n', '\n', texto)
        texto = re.sub(r'\n\s*CUBATÃO\s*\n', '\n', texto, flags=re.IGNORECASE)
        texto = re.sub(r'\nC[ÂA]MPUS\s*CUBATÃO\s*\n', '\n', texto, flags=re.IGNORECASE)
        texto = re.sub(r'\n\s*TÉCNICO EM [A-ZÀ-Ú ]+\s*\n', '\n', texto, flags=re.IGNORECASE)
        texto = re.sub(r'\n+', '\n', texto)
        texto = re.sub(r'[ \t]+', ' ', texto)
        texto = texto.replace('\n', ' ')
        texto = texto.strip()

        return texto

    @staticmethod
    def clean_save_json(text: list, output_path: str = 'dados_limpos.json') -> list:
        """
        Aplica limpeza nos campos de texto multilinha do JSON extraído e salva em arquivo.
        """
        logger.info("Iniciando limpeza dos dados...")

        for item in text:
            for field in MULTILINE_FIELDS:
                # verifica se existe no dicionário e se é string
                if field in item and isinstance(item[field], str):
                    original = item[field]
                    item[field] = TextCleaner.clean_text(original)
                    logger.debug(f"Campo '{field}' limpo.")

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(text, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON limpo salvo com sucesso: {output_path}")

            df = pd.DataFrame(text)
            df.to_csv("componentes_curriculares_extraidos.csv", index=False)



        except Exception as e:
            logger.error(f"Erro ao salvar o JSON limpo: {e}")
            raise

        return text