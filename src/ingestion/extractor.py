import json
import logging
import re
from typing import List, Dict, Any, LiteralString

import pandas as pd

from config.config import REGEX_FIELDS,MULTILINE_FIELDS

def extract_fields(texto: str) -> str | list[dict[Any, str | LiteralString]]:
    extracted_data = []
    sections = re.split(r"\b1-\s*IDENTIFICAÇÃO\b", texto)

    for section in sections[1:]:
        dados = {}
        for field, padrao in REGEX_FIELDS.items():
            flags = re.IGNORECASE | re.DOTALL if field in MULTILINE_FIELDS else re.IGNORECASE
            match = re.search(padrao, section, flags)

            if field == "Lab":
                if match:
                    sim = match.group(1).upper() if match.group(1) else ""
                    nao = match.group(2).upper() if match.group(2) else ""
                    if sim == 'X':
                        valor = "Sim"
                    elif nao == 'X':
                        valor = "Não"
                    elif match.lastindex >= 3 and match.group(3):
                        valor = f"{match.group(3).strip()}h"
                        if valor.endswith("h"):
                            valor = "Sim" if valor != "0h" else "Não"
                        elif valor == "não se aplica":
                            valor = "Não"
                    else:
                        valor = "Não se aplica"
                else:
                    valor = "Não se aplica"
            elif field == "Abordagem Metodológica":
                if match:
                    # Se não for vazio -> upper, caso seja vazio então coloca ""
                    t = match.group(1).upper() if match.group(1) else ""
                    p = match.group(2).upper() if match.group(2) else ""
                    tp_raw = match.group(3) or match.group(4)
                    tp = tp_raw.upper() if tp_raw else ""
                    if tp == 'X':
                        valor = "Teórica e Prática"
                    elif t == 'X':
                        valor = "Teórica"
                    elif p == 'X':
                        valor = "Prática"
                    else:
                        valor = "Nenhuma marcada"
                else:
                    # valor = match.group(1).strip()
                    valor = ""
            else:
                if match and match.lastindex and match.lastindex >= 1:
                    valor = match.group(1).strip()
                else:
                    valor = ""
            dados[field] = valor
            # dados[field] = match.group(1).strip() if match else ""
        if dados not in extracted_data:
            extracted_data.append(dados)

    with open("dados_brutos.json", "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=4)
    logging.debug("JSON gerado com sucesso: dados_brutos.json")

    print(type(extracted_data))



    return extracted_data