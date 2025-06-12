import json
import os
import fitz
import pandas as pd
import re
from collections import defaultdict

from documents import load_documents

def corrigir_blocos_emendados(texto):
    # Insere nova linha antes de seções importantes coladas
    texto = re.sub(r"(OBJETIVOS\s*[:\-]?)\s*(?=\n\d+\s*[-–]\s*[A-Z]|$)", r"\1\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"(CONTEÚDO\s+PROGRAMÁTICO\s*[:\-]?)\s*(?=\n\d+\s*[-–]\s*[A-Z]|$)", r"\1\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"(METODOLOGIA\s*[:\-]?)\s*(?=\n\d+\s*[-–]\s*[A-Z]|$)", r"\1\n", texto, flags=re.IGNORECASE)
    return texto

def remover_cabecalhos_rodapes(texto):
    # Remove linhas de rodapé isoladas (como antes)
    linhas = texto.splitlines()
    resultado = []
    for linha in linhas:
        linha_limpa = linha.strip()
        # if re.match(r'^\d{1,3}\s*$', linha_limpa):
        #     continue

        # Exceção: manter linha que começa com "Curso:"
        if linha_limpa.lower().startswith("Curso:"):
            match = re.match(r"(?i)curso:\s*(.*)", linha_limpa) # (?i) ignora maiúsculas/minúsculas
            if match:
                resultado.append(match.group(1))  # apenas o conteúdo depois de "Curso:"
            continue

        if len(linha_limpa) <= 80 and (
            re.fullmatch(r'(?i)CÂMPUS(\s+\w+)?', linha_limpa) or
            re.fullmatch(r'(?i)TÉCNICO EM [A-Z ]+', linha_limpa) or
            re.fullmatch(r'(?i)TECNOLOGIA EM [A-Z ]+', linha_limpa) or
            re.fullmatch(r'(?i)PROJETO PEDAGÓGICO DO CURSO.*', linha_limpa) or
            re.fullmatch(r'(?i)CBT.*', linha_limpa) or
            re.fullmatch(r'(?i)CURSO (TÉCNICO|SUPERIOR|DE) .*', linha_limpa)
        ):
            continue
        if re.fullmatch(r'(?i)CUBATÃO', linha_limpa):
            continue
        resultado.append(linha)

    texto_limpo = "\n".join(resultado)

    # Remover palavras-chave se estiverem no meio do texto
    texto_limpo = re.sub(r'\bTÉCNICO EM INFORMÁTICA INTEGRADO AO ENSINO MÉDIO\b', '', texto_limpo, flags=re.IGNORECASE)
    texto_limpo = re.sub(r'\bCUBATÃO\b', '', texto_limpo, flags=re.IGNORECASE)
    return texto_limpo

def normalizar_formatacao_multilinha(texto):
    # Remove múltiplos espaços e quebra de linha desnecessária
    texto = re.sub(r'\s*\n\s*', ' ', texto)  # junta linhas
    texto = re.sub(r'\s{2,}', ' ', texto)    # remove espaços duplos
    return texto.strip()



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

# for doc in documents:
#     nome_arquivo = os.path.basename(doc.metadata["source"])
#
#     texto_limpo = remover_cabecalhos_rodapes(doc.page_content)
#     documentos_agrupados[nome_arquivo] += texto_limpo + "\n"
#
#
# # #2. Limpa e junta as páginas
# texto_total = ""
# for doc in documents:
#     texto_limpo = remover_cabecalhos_rodapes(doc.page_content)
#     texto_total += texto_limpo + "\n"

#3. Corrigi blocos colados
# texto = corrigir_blocos_emendados(texto_total)

texto_total = ""
nome_arquivo = None  # inicializa nome_arquivo

for doc in documents:
    nome_arquivo = os.path.basename(doc.metadata["source"])
    texto_limpo = remover_cabecalhos_rodapes(doc.page_content)
    texto_total += texto_limpo + "\n"

texto = corrigir_blocos_emendados(texto_total)
secoes = re.split(r"\b1-\s*IDENTIFICAÇÃO\b", texto)

dados_extraidos = []

#for nome_arquivo, texto_doc in documentos_agrupados.items():
# # .split: assim que ele encontrar o identificador ele "divide"
#secoes = re.split(r"\b1-\s*IDENTIFICAÇÃO\b", texto)
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

with open("componentes_curriculares_extraidos.json", "w", encoding="utf-8") as f_json:
    json.dump(dados_extraidos, f_json, ensure_ascii=False, indent=4)
print("JSON gerado com sucesso: componentes_curriculares_extraidos.json")


df = pd.DataFrame(dados_extraidos)
df.to_csv("componentes_curriculares_extraidos.csv", index=False)

print("CSV gerado com sucesso: componentes_curriculares_extraidos.csv")