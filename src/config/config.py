"""
  - Caminhos (diretórios de documentos, logs, etc)
  - Arquivos fixos
  - Algoritmos padrão (como sha256)
  - Configurações reutilizadas por várias partes do sistema
"""

from pathlib import Path

# Diretórios
BASE_DIR = Path(__file__).resolve().parent.parent.parent # Aqui ele traça onde ta o arquico com base na os

DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "docs"
HASH_FILE = DATA_DIR / "docs_hash.json"
CHROMA_DIR = BASE_DIR / "chroma_db"
FOLDER_PATH = "data/docs"

# Outras configs
# EMBEDDING_MODEL = "all-MiniLM-L6-v2"
# CHUNK_SIZE = 1000
# CHUNK_OVERLAP = 200

# Dados

REGEX_FIELDS = {
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

MULTILINE_FIELDS = {
    "Grupos de Conhecimentos Essenciais",
    "Ementa",
    "Objetivos",
    "Conteúdo Programático"
}



