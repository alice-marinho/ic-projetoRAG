import json
from utils.logger import setup_logger
import re
from typing import List, Dict, Any, LiteralString, Optional

import pandas as pd

from config import config
from config.config import REGEX_FIELDS,MULTILINE_FIELDS

class DocsExtractor:
    def __init__(
        self,
        raw_data_file = config.RAW_DATA_FILE,
    ):
        self.raw_data_file = raw_data_file


    def extract_fields(self, texto: str)-> list[dict[Any, str | LiteralString]]:
        extracted_data = []
        logger = setup_logger(__name__)

        # Ele vai procurar "Planos de ensino" somente se tiver em seguida de 1- Identificação

        start_pattern = r"(?s)(Planos de ensino.*?1-\s*IDENTIFICAÇÃO.*)"
        match_planos = re.search(start_pattern, texto, re.IGNORECASE)  # DOTALL já está no (?s)

        if not match_planos:
            logger.warning("Seção 'Planos de ensino' seguida por '1- IDENTIFICAÇÃO' não encontrada.")
            return []  # Retorna lista vazia se não encontrar a seção
        # Divide o texto em seções
        sections = re.split(r"\b1-\s*IDENTIFICAÇÃO\b", texto)

        # Extrai o conteúdo de cada seção
        for section in sections[1:]:
            dados = {}
            for field, padrao in REGEX_FIELDS.items():
                flags = re.IGNORECASE | re.DOTALL if field in MULTILINE_FIELDS else re.IGNORECASE
                match = re.search(padrao, section, flags)

                if field == "Lab":
                   valor = self._parse_lab_field(match)
                elif field == "Abordagem Metodológica":
                    valor = self._parse_abordagem_field(match)
                else:
                    if match and match.lastindex and match.lastindex >= 1:
                        valor = match.group(1).strip()
                    else:
                        valor = ""
                dados[field] = valor
                  #  dados[field] = valor
                # dados[field] = match.group(1).strip() if match else ""

            if dados not in extracted_data:
                extracted_data.append(dados)
        with open(self.raw_data_file, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        logger.debug("JSON gerado com sucesso: dados_brutos.json")

        # print(type(extracted_data))

        return extracted_data

    @staticmethod
    def _parse_lab_field(match: Optional[re.Match]) -> str:
        if not match:
            return "Não se aplica"

        sim = match.group(1).upper() if match.group(1) else ""
        nao = match.group(2).upper() if match.group(2) else ""
        if sim == 'X':
            return "Sim"
        elif nao == 'X':
            return "Não"
        elif match.lastindex is not None and match.lastindex >= 3 and match.group(3):
            valor = f"{match.group(3).strip()}h"
            if valor.endswith("h"):
                return "Sim" if valor != "0h" else "Não"
            elif valor == "não se aplica":
                return "Não"
        else:
            return "N/A"

    """
    Optional = match pode ser None quando a regex não encontrou resultado, 
    e o método vai retornar valor padrão seguro.
    """
    def _parse_abordagem_field(self, match: Optional[re.Match]) -> str:
        if not match:
            return "N/A"

        # Se não for vazio -> upper, caso seja vazio então coloca ""
        t = match.group(1).upper() if match.group(1) else ""
        p = match.group(2).upper() if match.group(2) else ""
        tp_row = match.group(3) or match.group(4)
        tp = tp_row.upper() if tp_row else ""
        if tp == 'X':
            return "Teórica e Prática"
        elif t == 'X':
            return "Teórica"
        elif p == 'X':
            return "Prática"
        else:
            return "Nenhuma marcada"
