import json
import os
import numpy as np
import pandas as pd
import re
from collections import defaultdict

from documents import load_documents


FOLDER_PATH = "data/docs"

regex_campos = {
    # (.*) ele retorna tudo o que vem depois de encontrar
    "Curso": r"Curso:\s*(.*)",
    "Componente curricular": r"(?:Componente:|Componente curricular:)\s*(.*)",
    "Semestre": r"Semestre:\s*(\d+)",
    "Ano": r"Ano:\s*(\d+)",
    "Código": r"(?:Código:|Sigla:)\s*(.*)",
    "Tipo": r"Tipo:\s*(.*)",
    "Núcleo": r"(?:Núcleo:|Nucleo:)\s*(.*)",
    "N° de docentes": r"(?:quantidade|[Nn]\.?\°?\s*\.?|número)?\s*(?:de)?\s*docente[s]?:\s*(\d*)",
    "Nº de aulas semanais": r"(?:quantidade de|n\.?\s*°?\s*|n\.?\s*°?\s*de|número de)?\s*aulas \s*semanais[:\s]*\s*(\d+)",
    "Total de aulas": r"Total de aulas:\s*(\d+)",
    "C.H. Ensino": r"C\.H\. Ensino:\s*(\d+[.,]?\d*)",
    "C.H. Presencial": r"C\.H\. Presencial:\s*(.*)",
    "Abordagem Metodológica": r"""T\s*\(\s*([Xx])?\s*\)\s*P\s*\(\s*([Xx])?\s*\)\s*(?:T/P\s*\(\s*([Xx])?\s*\)|\(\s*([Xx])?\s*\)\s*T/P)""",
    "Lab": r"(?:\(\s*([Xx])?\s*\)\s*SIM\s*\(\s*([Xx])?\s*\)\s*N[ÃA]O|(?:carga.*)laborat[óo]rio[:\s]*\n*\s*(\d+[.,]?\d*))", #r"(?:Uso de.*?laboratório|Carga horária.*?laboratório).*?[:\?]\s*(.*)"
    "Grupos de Conhecimentos Essenciais": r"2\s*-\s*(?:GRUPOS\s+DE\s+)?Conhecimentos essenciais do curr[íi]culo de refer[êe]ncia\s*:?\s*(.*?)(?=\n?\s*\d+\s*-\s*)",
    "Ementa": r"Ementa\s*[:\-]?\s*(.*?)(?=\n\d+\s*[-–—]\s*[A-Z]|(?=4\s*-\s*OBJETIVOS|$))",
    "Objetivos": r"OBJETIVOS\s*[:\-–—]?\s*(.*?)(?=\n\d+\s*[-–—]\s*[A-Z]|(?=\n\d+\s*[-–—]\s*ÁREAS DE INTEGRAÇÃO))",
    "Conteúdo Programático": r"5\s*[-–]\s*CONTEÚDO\s+PROGRAMÁTICO\s*[:\-]?\s*(.*?)(?=\n?6\s*[-–]\s*(?:METODOLOGIA|BIBLIOGRAFIA)|$)"
}


campos_multilinha = {
    "Grupos de Conhecimentos Essenciais",
    "Ementa",
    "Objetivos",
    "Conteúdo Programático"
}


dados_extraidos = []

# 1. Carrega
documents = load_documents()

# 2. Agrupar texto por nome de arquivo
documentos_agrupados = defaultdict(str)

texto_total = ""

for doc in documents:
    nome_arquivo = os.path.basename(doc.metadata["source"])
    texto_total += doc.page_content + "\n"

#texto = corrigir_blocos_emendados()
secoes = re.split(r"\b1-\s*IDENTIFICAÇÃO\b", texto_total)

dados_extraidos = []


for secao in secoes[1:]:
    #dados = {"Fonte": nome_arquivo}
    dados = {}
    for campo, padrao in regex_campos.items():
        flags = re.IGNORECASE | re.DOTALL if campo in campos_multilinha else re.IGNORECASE
        match = re.search(padrao, secao, flags)
        if campo == "Lab":
            if match:
                sim = match.group(1).upper() if match.group(1) else ""
                nao = match.group(2).upper() if match.group(2) else ""
                if sim == 'X':
                    valor = "Sim"
                elif nao == 'X':
                    valor = "Não"
                elif match.lastindex >= 3 and match.group(3):
                    valor = f"{match.group(3).strip()}h"
                else:
                    valor = "Não se aplica"
            else:
                valor = "Não se aplica"
        elif campo == "Abordagem Metodológica":
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
                #valor = match.group(1).strip()
                valor = ""
        else:
            if match and match.lastindex and match.lastindex >= 1:
                valor = match.group(1).strip()
            else:
                valor = ""
        dados[campo] = valor
        # dados[campo] = match.group(1).strip() if match else ""
    if dados not in dados_extraidos:
        dados_extraidos.append(dados)

# w - write | "r" - read | "a" - append
with open("componentes_curriculares_extraidos.json", "w", encoding="utf-8") as f_json:
    json.dump(dados_extraidos, f_json, ensure_ascii=False, indent=4)
print("JSON gerado com sucesso: componentes_curriculares_extraidos.json")


import re

def limpar_texto(texto):
    if not texto:
        return texto

    # Remove "Projeto Pedagógico do Curso ..." em qualquer lugar da linha até \n
    texto = re.sub(r'(?i)Projeto Pedagógico do Curso.*?\n', '', texto)

    # Remove "Tecnologia em ..." em qualquer lugar da linha até \n
    texto = re.sub(r'(?i)Tecnologia em .*?\n', '', texto)

    # Remove números isolados mesmo entre várias quebras e espaços (\n \n 65 \n \n)
    texto = re.sub(r'\n\s*\d+\s*\n', '\n', texto)

    # Remove "CUBATÃO" isolado entre quebras de linha e espaços (ex: \n \n CUBATÃO \n \n)
    texto = re.sub(r'\n\s*CUBATÃO\s*\n', '\n', texto, flags=re.IGNORECASE)

    texto = re.sub(r'\nC[ÂA]MPUS\s*CUBATÃO\s*\n', '\n', texto, flags=re.IGNORECASE)

    # Remove linhas que sejam só "TÉCNICO EM ..." entre quebras (com possíveis espaços)
    texto = re.sub(r'\n\s*TÉCNICO EM [A-ZÀ-Ú ]+\s*\n', '\n', texto, flags=re.IGNORECASE)

    # Remove múltiplas quebras de linha consecutivas e substitui por uma só
    texto = re.sub(r'\n+', '\n', texto)

    # Remove espaços e tabs extras
    texto = re.sub(r'[ \t]+', ' ', texto)

    texto = texto.replace('\n', ' ')

    # Remove espaços no início e fim
    texto = texto.strip()

    return texto


with open('componentes_curriculares_extraidos.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)

campos_texto = ["Grupos de Conhecimentos Essenciais", "Ementa", "Objetivos", "Conteúdo Programático"]
for item in dados:
    for campo in campos_texto:
        if campo in item:
            item[campo] = limpar_texto(item[campo])

# Salva o JSON limpo
with open('dados_limpos.json', 'w', encoding='utf-8') as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)

df = pd.DataFrame(dados_extraidos)

df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
df.fillna(' - ', inplace=True)

df.to_csv("componentes_curriculares_extraidos.csv", index=False)
df.to_json("dados_tratados.json", orient="records", indent=2, force_ascii=False)


print("CSV gerado com sucesso: componentes_curriculares_extraidos.csv")

