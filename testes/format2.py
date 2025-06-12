import re
import pandas as pd
from documents import load_documents

# Remove cabeçalhos e rodapés
def remover_cabecalhos_rodapes(texto):
    linhas = texto.splitlines()
    resultado = []
    for linha in linhas:
        linha_limpa = linha.strip()
        if re.match(r'^\d{1,3}\s*$', linha_limpa):
            continue
        if len(linha_limpa) <= 80 and (
            re.fullmatch(r'(?i)CÂMPUS(\s+\w+)?', linha_limpa) or
            re.fullmatch(r'(?i)TÉCNICO EM [A-Z ]+', linha_limpa) or
            re.fullmatch(r'(?i)TECNOLOGIA EM [A-Z ]+', linha_limpa) or
            re.fullmatch(r'(?i)PROJETO PEDAGÓGICO DO CURSO.*', linha_limpa) or
            re.fullmatch(r'(?i)CURSO (TÉCNICO|SUPERIOR|DE) .*', linha_limpa) or
            re.fullmatch(r'(?i)CUBATÃO', linha_limpa)
        ):
            continue
        resultado.append(linha)

    texto_limpo = "\n".join(resultado)
    texto_limpo = re.sub(r'\bTÉCNICO EM INFORMÁTICA INTEGRADO AO ENSINO MÉDIO\b', '', texto_limpo, flags=re.IGNORECASE)
    texto_limpo = re.sub(r'\bCUBATÃO\b', '', texto_limpo, flags=re.IGNORECASE)
    return texto_limpo

# Corrige blocos colados
def corrigir_blocos_emendados(texto):
    texto = re.sub(r"(OBJETIVOS\s*[:\-]?)\s*(5\s*[-–]\s*CONTEÚDO)", r"\1\n\2", texto, flags=re.IGNORECASE)
    texto = re.sub(r"(CONTEÚDO\s+PROGRAMÁTICO\s*[:\-]?)\s*(6\s*[-–]\s*METODOLOGIA)", r"\1\n\2", texto, flags=re.IGNORECASE)
    texto = re.sub(r"(METODOLOGIA\s*[:\-]?)\s*(7\s*[-–]\s*AVALIAÇÃO)", r"\1\n\2", texto, flags=re.IGNORECASE)
    texto = re.sub(r"(AVALIAÇÃO\s*[:\-]?)\s*(8\s*[-–]\s*BIBLIOGRAFIA)", r"\1\n\2", texto, flags=re.IGNORECASE)
    texto = re.sub(r"(BIBLIOGRAFIA(?:\s*BÁSICA)?\s*[:\-]?)\s*(9\s*[-–]\s*BIBLIOGRAFIA\s+COMPLEMENTAR)", r"\1\n\2", texto, flags=re.IGNORECASE)
    return texto

# Campos e regex
regex_campos = {
    "Curso": r"Curso:\s*(.*)",
    "Componente curricular": r"(?:Componente:|Componente curricular:)\s*(.*)",
    "Semestre": r"Semestre:\s*(\d+)",
    "Ano": r"Ano:\s*(\d+)",
    "Código": r"(?:Código:|Sigla:)\s*(.*)",
    "Tipo": r"Tipo:\s*(.*)",
    "Núcleo": r"(?:Núcleo:|Nucleo:)\s*(.*)",
    "N° de docentes": r"(?:quantidade de|n[°] de|número de)?\s*docentes:\s*(\d+)",
    "Nº de aulas semanais": r"(?:quantidade de|n\.?\s*°?\s* de|número de)?\s*aulas\s*semanais[:\s]*\s*(\d+)",
    "Total de aulas": r"Total de aulas:\s*(\d+)",
    "C.H. Ensino": r"C\.H\. Ensino:\s*(\d+[.,]?\d*)",
    "C.H. Presencial": r"C\.H\. Presencial:\s*(.*)",
    "Abordagem Metodológica": r"""T\s*\(\s*([Xx])?\s*\)\s*P\s*\(\s*([Xx])?\s*\)\s*(?:T/P\s*\(\s*([Xx])?\s*\)|\(\s*([Xx])?\s*\)\s*T/P)""",
    "Lab": r"",  # tratado à parte
    "Grupos de Conhecimentos Essenciais": r"2\s*-\s*(?:GRUPOS\s+DE\s+)?Conhecimentos.*?:\s*(.*?)(?=\n?\s*\d+\s*-\s*)",
    "Ementa": r"Ementa\s*[:\-]?\s*(.*?)(?=4\s*-\s*OBJETIVOS|$)",
    "Objetivos": r"4\s*-\s*OBJETIVOS\s*[:\-]?\s*(.*?)(?=\n?5\s*[-–]\s*CONTEÚDO\s+PROGRAMÁTICO|$)",
    "Conteúdo Programático": r"5\s*[-–]\s*CONTEÚDO\s+PROGRAMÁTICO\s*[:\-]?\s*(.*?)(?=\n?6\s*[-–]\s*(?:METODOLOGIA|BIBLIOGRAFIA)|$)",
    "Metodologia": r"6\s*[-–]?\s*METODOLOGIA\s*[:\-]?\s*(.*?)(?=\n?\s*7\s*[-–]?\s*AVALIAÇÃO|$)",
    "Avaliação": r"7\s*[-–]?\s*AVALIAÇÃO\s*[:\-]?\s*(.*?)(?=\s*8\s*[-–]?\s*BIBLIOGRAFIA|$)",
    "Bibliografia": r"8\s*[-–]?\s*BIBLIOGRAFIA(?:\s*BÁSICA)?\s*[:\-]?\s*(.*?)(?=\s*9\s*[-–]?\s*BIBLIOGRAFIA\s+COMPLEMENTAR|$)",
    "Bibliografia Complementar": r"9\s*[-–]?\s*BIBLIOGRAFIA\s+COMPLEMENTAR\s*[:\-]?\s*(.*?)(?=\s*\d+\s*[-–]|$)"
}

campos_multilinha = {
    "Grupos de Conhecimentos Essenciais", "Ementa", "Objetivos", "Conteúdo Programático",
    "Metodologia", "Avaliação", "Bibliografia"
}

# 1. Carrega páginas
documents = load_documents()

# 2. Limpa e junta as páginas
texto_total = ""
for doc in documents:
    texto_limpo = remover_cabecalhos_rodapes(doc.page_content)
    texto_total += texto_limpo + "\n"

# 3. Corrige blocos colados
texto_corrigido = corrigir_blocos_emendados(texto_total)


 # 4. Divide por componente
componentes = re.split(r"\b1-\s*IDENTIFICAÇÃO\b", texto_corrigido)[1:]

with open("meu_arquivo2.txt", "w", encoding="utf-8") as arquivo:
    arquivo.write(texto_corrigido)
#
# # 5. Extrai os dados
# dados_extraidos = []
# for secao in componentes:
#     dados = {"Fonte": "PPC"}
#     for campo, padrao in regex_campos.items():
#         flags = re.IGNORECASE | re.DOTALL if campo in campos_multilinha else re.IGNORECASE
#         match = re.search(padrao, secao, flags)
#
#         if campo == "Lab":
#             regex_lab = re.search(
#                 r"""Uso de.*?laboratório.*?\?\s*
#                     .*?\(\s*(?P<sim>X)?\s*\)\s*SIM\s*\(\s*(?P<nao>X)?\s*\)\s*NÃO
#                     (?:.*?C\.?H\.?\s*[:\-]?\s*(?P<ch>[\d]+))?
#                     (?:.*?Qual\(is\)\s*[:\-]?\s*(?P<local>[^\n]+))?
#                 """,
#                 secao,
#                 re.IGNORECASE | re.DOTALL | re.VERBOSE,
#             )
#             if regex_lab:
#                 if regex_lab.group("sim"):
#                     ch = regex_lab.group("ch") or ""
#                     local = regex_lab.group("local") or ""
#                     valor = f"SIM | C.H.: {ch} | Local: {local}".strip()
#                 else:
#                     valor = "NÃO"
#             else:
#                 valor = ""
#         elif campo == "Abordagem Metodológica":
#             if match:
#                 t = match.group(1).upper() if match.group(1) else ""
#                 p = match.group(2).upper() if match.group(2) else ""
#                 tp_raw = match.group(3) or match.group(4)
#                 tp = tp_raw.upper() if tp_raw else ""
#                 if tp == 'X':
#                     valor = "Teórica e Prática"
#                 elif t == 'X':
#                     valor = "Teórica"
#                 elif p == 'X':
#                     valor = "Prática"
#                 else:
#                     valor = "Nenhuma marcada"
#             else:
#                 valor = ""
#         else:
#             valor = match.group(1).strip() if match else ""
#         dados[campo] = valor
#     dados_extraidos.append(dados)
#
# # 6. Gera CSV com tratamento de quebra de linha
# df = pd.DataFrame(dados_extraidos)
#
# # Substitui \n dentro das células para não quebrar no CSV
# for col in df.columns:
#     if df[col].dtype == "object":
#         df[col] = df[col].str.replace('\n', '\\n')
#
# # Não remove os \n, deixa como quebra real
# df.to_csv("componentes_curriculares.csv", index=False, encoding='utf-8-sig', quotechar='"', lineterminator='\r\n')
#
# print("✅ CSV gerado com sucesso!")
