import os
import re
import json
from dotenv import load_dotenv

import fitz  # PyMuPDF
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from together import Together


# ---------- PARTE 1 - EXTRAÇÃO E LIMPEZA DO JSON ----------

FOLDER_PATH = "../data/docs"
CHROMA_DIR = "chroma_db"

# Regex para extrair campos dos textos
regex_campos = {
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
    "Lab": r"(?:\(\s*([Xx])?\s*\)\s*SIM\s*\(\s*([Xx])?\s*\)\s*N[ÃA]O|(?:carga.*)laborat[óo]rio[:\s]*\n*\s*(\d+[.,]?\d*))",
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


def load_documents():
    """
    Carrega os documentos PDF da pasta e retorna lista de Document do LangChain
    """
    if not os.path.exists(FOLDER_PATH):
        raise FileNotFoundError(f"Pasta não encontrada: {FOLDER_PATH}")

    docs = []
    for filename in os.listdir(FOLDER_PATH):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(FOLDER_PATH, filename)
            pdf = fitz.open(path)
            for i, page in enumerate(pdf):
                text = page.get_text()
                if text.strip():
                    docs.append(Document(page_content=text, metadata={"source": filename, "page": i + 1}))
    if not docs:
        raise ValueError("Nenhum documento PDF válido encontrado na pasta.")
    return docs


def extract_and_save_json():
    """
    Extrai informações dos PDFs usando regex e salva no JSON.
    """
    documents = load_documents()

    texto_total = ""
    for doc in documents:
        texto_total += doc.page_content + "\n"

    secoes = re.split(r"\b1-\s*IDENTIFICAÇÃO\b", texto_total)
    dados_extraidos = []

    for secao in secoes[1:]:
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
                    valor = ""
            else:
                if match and match.lastindex and match.lastindex >= 1:
                    valor = match.group(1).strip()
                else:
                    valor = ""
            dados[campo] = valor

        if dados not in dados_extraidos:
            dados_extraidos.append(dados)

    with open("componentes_curriculares_extraidos.json", "w", encoding="utf-8") as f:
        json.dump(dados_extraidos, f, ensure_ascii=False, indent=4)
    print("JSON gerado com sucesso: componentes_curriculares_extraidos.json")
    return dados_extraidos


def limpar_texto(texto):
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


def clean_and_save_json(dados):
    """
    Aplica limpeza nos campos de texto multilinha do JSON extraído e salva.
    """
    campos_texto = [
        "Grupos de Conhecimentos Essenciais",
        "Ementa",
        "Objetivos",
        "Conteúdo Programático"
    ]
    for item in dados:
        for campo in campos_texto:
            if campo in item:
                item[campo] = limpar_texto(item[campo])

    with open('dados_limpos.json', 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print("JSON limpo salvo com sucesso: dados_limpos.json")
    return dados


# ----------  EMBEDDING E BANCO VETORIAL ----------

load_dotenv()
client = Together()
client.api_base = "https://api.together.xyz/v1"


# def create_chunks_from_json(dados_limpos):
#     """
#     Cria uma lista de Document para embedding a partir do JSON limpo.
#     Cada item vira um chunk concatenando seus campos.
#     """
#     documents = []
#     for item in dados_limpos:
#         texto = ""
#         for k, v in item.items():
#             if v:
#                 texto += f"{k}: {v}\n"
#         texto = texto.strip()
#         if texto:
#             documents.append(Document(page_content=texto, metadata={"source": "componentes_curriculares_extraidos.json"}))
#     return documents

def create_chunks_from_json(dados_limpos):
    """
    Cria chunks separados por blocos principais de cada item do JSON.
    Gera chunks separados para:
        - Metadados gerais
        - Grupos de Conhecimentos Essenciais
        - Ementa
        - Objetivos
        - Conteúdo Programático
    """
    documents = []

    for item in dados_limpos:
        # Chunk com os metadados principais
        metadados = []
        for campo in ["Curso", "Componente curricular", "Semestre", "Ano", "Código", "Tipo", "Núcleo",
                      "N° de docentes", "Nº de aulas semanais", "Total de aulas", "C.H. Ensino",
                      "C.H. Presencial", "Abordagem Metodológica", "Lab"]:
            valor = item.get(campo, "")
            if valor:
                metadados.append(f"{campo}: {valor}")

        texto_metadados = "\n".join(metadados)
        documents.append(Document(page_content=texto_metadados, metadata={"source": "componentes_curriculares_extraidos.json"}))

        # Chunks para os blocos principais se existirem
        for bloco in ["Grupos de Conhecimentos Essenciais", "Ementa", "Objetivos", "Conteúdo Programático"]:
            valor = item.get(bloco, "").strip()
            if valor:
                chunk_text = f"{bloco}:\n{valor}"
                documents.append(Document(page_content=chunk_text, metadata={"source": "componentes_curriculares_extraidos.json"}))

    return documents

def create_vector_store(documents):
    """
    Cria e salva banco vetorial Chroma usando embeddings HuggingFace.
    """
    embeddings = HuggingFaceEmbeddings()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=600,
        separators=["\n\n", "}"])
    docs_split = splitter.split_documents(documents)

    vectordb = Chroma.from_documents(docs_split, embeddings, persist_directory=CHROMA_DIR)

    print("Banco vetorial criado e salvo em", CHROMA_DIR)
    return vectordb

def summarize_question(question):
   # prompt = (f"Forneça a melhor versão da minha pergunta. Verifique se eu elaborei a melhor versão dela, se não, sugira para mim a melhor versão."
   #           f"\n\n{question}")

    prompt = (
       "Reformule a pergunta abaixo apenas se ela estiver mal escrita, incompleta ou confusa. "
       "Caso já esteja clara e direta no contexto educacional, responda apenas com 'OK'\n\n"
       f"{question}"
    )


    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    content = response.choices[0].message.content.strip()


    # Se a IA respondeu apenas "OK", usamos a pergunta original
    if content.strip().upper() == "OK":
        return question
        # Se a resposta parece ser uma explicação (e não uma pergunta), usamos a original também
    elif "?" not in content or len(content.split()) > 20:
        return question
    else:
        return content


def similarity_search(vectordb, query, k=3):
    """
    Busca similaridade no banco vetorial.
    """
    results = vectordb.similarity_search(query, k=k)
    return results

def generate_response(question, context, history):
    final_context = "\n\n".join(context)

    conversation_history = ""
    for troca in history:
        conversation_history += f"Usuário: {troca['pergunta']}\n"
        conversation_history += f"IA: {troca['resposta']}\n"

    prompt = f"""
    Você é uma inteligência artificial que responde perguntas estritamente com base no contexto abaixo.

    ================ CONTEXTO =================
    {final_context}
    ===========================================

    Instruções:
    - Responda sempre em Português - BR
    - Se o contexto incluir uma lista de tópicos ou conteúdos que claramente pertencem a uma disciplina (mesmo que o nome da disciplina não esteja explícito), associe-os ao nome da disciplina mencionada na pergunta.
    - Associe temas da pergunta ao conteúdo programático das disciplinas descritas.
    - Responda à pergunta abaixo usando somente o conteúdo do CONTEXTO.
    - Se o conteúdo da resposta estiver claramente no CONTEXTO, apresente a resposta diretamente.
    - Se a informação **não** estiver no CONTEXTO, diga: "A informação não está disponível nos arquivos analisados."
    - **Não use conhecimento externo**.

    Histórico da conversa (para contexto):
    {conversation_history}

    Pergunta: {question}
    """
    #prompt
    # prompt = f"""
    # Você é uma inteligência artificial especializada em auxiliar no contexto educacional.
    #
    # Histórico da conversa até agora:
    # {conversation_history}
    #
    # Sua base de dados principal será essa: {final_context}
    #
    # Sua função é:
    # - Responder perguntas sobre conteúdos, disciplinas, materiais didáticos e temas educacionais.
    # - Sugerir ideias, conteúdos e abordagens para projetos acadêmicos, se aplicável.
    #
    # Regras:
    # - Use estritamente o plano de aula como base principal de informações.
    # - Só adicione informações externas se forem altamente relevantes para educação ou projetos.
    # - Utilize linguagem clara, acessível e mantenha coerência no diálogo.
    # - Nunca responda perguntas fora do contexto educacional.
    # - Se a pergunta for confusa ou fora do escopo, responda: "Pode explicar novamente?"
    #
    # Pergunta: {question}
    # Resposta:
    # """

    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[
            {"role": "system", "content": "Você responde com base apenas no contexto fornecido."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()

HASH_FILE = "docs_hash.json"
def calculate_docs_hash(docs_dir):
    hash_md5 = hashlib.md5()
    for root, _, files in os.walk(docs_dir):
        for f in sorted(files):
            path = os.path.join(root,f)
            with open(path, "rb") as file:
                while chunk := file.read(4096):
                    hash_md5.update(chunk)
    return hash_md5.hexdigest()

def has_docs_changed():
    current_hash = calculate_docs_hash("../data/docs")
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            saved_hash = json.load(f).get("hash")
        if saved_hash == current_hash:
            return False
    # Save new hash
    with open(HASH_FILE, "w") as f:
        json.dump({"hash": current_hash}, f)
    return True


def main():
    # 1) Extrair e limpar dados dos PDFs
    dados_extraidos = extract_and_save_json()
    dados_limpos = clean_and_save_json(dados_extraidos)

    # 2) Criar documentos para embedding a partir do JSON limpo
    documents = create_chunks_from_json(dados_limpos)

    # 3) Criar ou carregar banco vetorial
    if not os.path.exists(CHROMA_DIR):
        vectordb = create_vector_store(documents)
    else:
        embeddings = HuggingFaceEmbeddings()
        vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        print(f"Banco vetorial carregado de {CHROMA_DIR}")

    # 4) Loop de interação com o usuário
    conversation_history = []

    print("\nSistema de Perguntas e Respostas iniciado. Digite 'sair' para encerrar.\n")

    while True:
        question = input("Pergunte sobre (ou 'sair'): ")
        if question.lower() == "sair":
            break
        if not question.strip():
            print("Digite uma pergunta válida.")
            continue

        # Busca no banco vetorial
        resultados = similarity_search(vectordb, question, k=3)

        if not resultados:
            print("Nenhum contexto encontrado.")
            continue

        # Combinar os contextos em um só texto
        context = "\n".join([doc.page_content for doc in resultados])

        # Gerar resposta simples
        resposta = f"Contexto encontrado:\n{context}"

        # Armazenar no histórico
        conversation_history.append({"pergunta": question, "resposta": resposta})

        # Exibir resposta
        print(f"\nResposta da IA:\n{resposta}\n")


if __name__ == "__main__":
    main()
