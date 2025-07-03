from collections import Counter
from utils.logger import setup_logger
from llm import LLMClient
from keybert import KeyBERT

import spacy


def extract_keywords(text, top_n=5):
    # Extração com KeyBERT
    keybert_kws = extract_with_keybert(text, top_n)
    print(keybert_kws)

    # Extração com spaCy
    spacy_kws = extract_with_spacy(text)
    print(spacy_kws)

    # Consolida os resultados
    all_kws = Counter(keybert_kws + spacy_kws)
    ranked_kws = [kw for kw, _ in all_kws.most_common(top_n * 2)]

    # Refina com contexto educacional
    refined_kws = refine_keywords_llm(text, ranked_kws)

    return refined_kws[:top_n]

def expand_question_with_keywords(question, keywords):
    """
    Adiciona palavras-chave à pergunta reformulada para enriquecer o embedding.
    """
    keyword_str = " ".join(keywords)
    return f"{question} Palavras-chave: {keyword_str}"

def summarize_question(question):
    """
    Reformula a pergunta caso esteja mal escrita, incompleta ou confusa.
    Sempre oferece a versão original e a versão sugerida para escolha.

    Args:
        question (str): Pergunta original.

    Returns:
        str: Pergunta reformulada.
    """

    prompt = (
        "Você é uma especialista em Processamento de Linguagem Natural. "
        "Sua tarefa é reformular a frase abaixo, de modo imperativo, para torná-la clara, objetiva e tecnicamente "
        "correta, "
        "mas sem remover termos importantes como nomes de disciplinas, tecnologias, autores, datas, ou exemplos citados. "
        "A reformulação deve preservar todos os elementos essenciais da pergunta original e manter o foco no contexto educacional. "
        "Responda apenas com a versão reformulada da pergunta, sem explicações ou comentários. "
        "Pergunta original:\n\n"
        f"{question}"
    )
    # prompt = (
    #     "Aja como um especialista em processamento de linguagem natural. "
    #     "Para todas as minhas perguntas, dê a melhor versão delas e ao final me permita escolher entre a sua e a minha. "
    #     "Somente melhore, não me dê informações ou respostas das perguntas"
    #     "Responda apenas com a pergunta reformulada, sem explicações e tudo em Português - BR."
    #     "Aqui está a pergunta:\n\n"
    #     f"{question}"
    # )

    llm_client = LLMClient()
    suggested_question = llm_client.chat(prompt)

    print(f"\nSugestão de reformulação: {suggested_question}")
    choice = input("Deseja usar a versão sugerida? (s/n): ").strip().lower()

    if choice == 's':
        return suggested_question
    else:
        return question

def extract_with_keybert(text, top_n):
    """
    Utilizando a KeyBERT que é baseado em embeddings que tem como foco encontrar similaridade
    entre vetores semânticos

    :param text: Pergunta do usuário para retirar as palavras chaves
    :param top_n: Quantidade máxima de palavras chaves
    :return: As palavras chaves extraídas
    """
    kw_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
    keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1,2), # Palavras únicas ou duplas
        top_n=top_n
    )
    print("[DEBUG] Raw keywords:", keywords)
    return [kw[0] for kw in keywords]


def extract_with_spacy(text):
    logger = setup_logger(__name__)
    try:
        nlp = spacy.load("pt_core_news_sm")
        doc = nlp(text)

        chunks = set()
        for chunk in doc.noun_chunks:
            # texto (str) de cada token
            filtered_tokens = [
                token.text for token in chunk
                if not token.is_stop
                   and len(token.text) > 2
                   and token.pos_ in ['NOUN', 'PROPN', 'ADJ']
            ]

            filtered_chunk = "".join(filtered_tokens).strip()
            if filtered_chunk:
                chunks.add(filtered_chunk)

        return list(chunks)
    except Exception as e:
        logger.warning(f"[ERROR] SpaCy extraction failed: {e}")
        return []


def refine_keywords_llm(original_text, raw_keywords):
    """
    Envia as palavras-chave extraídas para a LLM e pede que as refine,
    organize e priorize com base no texto original.
    """
    prompt = f"""
    [CONTEXTO EDUCACIONAL] Analise estas palavras-chave considerando que o texto vem de um ambiente acadêmico:
        
        TEXTO ORIGINAL: "{original_text}"
        
        PALAVRAS-CHAVE: {raw_keywords}
        
        TAREFA:
    1. Filtre mantendo APENAS termos técnicos relevantes para educação
    2. Priorize nesta ordem:
       - Nomes de disciplinas (ex: Matemática 1)
       - Técnicas/conceitos (ex: derivadas parciais)
       - Tecnologias (ex: Python)
    3. Formate como LISTA PURA, 1 item por linha, sem numeração ou prefixos
    4. Exemplo de saída válida:
       algoritmos
       matemática discreta
       complexidade computacional

    SAÍDA (APENAS OS TERMOS, SEM COMENTÁRIOS):

        """
        # Você é uma inteligência artificial especialista em educação e processamento de linguagem natural.
        #
        # Recebeu o seguinte texto original:
        # ---
        # {original_text}
        # ---
        #
        # E as palavras-chave extraídas automaticamente foram:
        # {', '.join(raw_keywords)}
        #
        # Sua tarefa é:
        # - Corrigir e refinar essas palavras-chave com base no significado real do texto original.
        # - Priorize termos relacionados a disciplinas, matérias, anos, conteúdos específicos, tecnologias, autores e quaisquer elementos citados relevantes no contexto educacional.
        # - Remova repetições, palavras genéricas ou irrelevantes que não agreguem valor para compreensão do contexto.
        # - Retorne uma lista de no máximo 10 palavras-chave ou expressões curtas (2 a 4 palavras no máximo), separadas por vírgula, em português do Brasil.
        # - Apenas a lista, sem explicações ou comentários adicionais.
        # """

    try:
        llm = LLMClient()
        response = llm.chat(prompt)
        # Pós-processamento robusto
        return [
            kw.strip().lower()
            for kw in response.split('\n')
            if kw.strip() and len(kw.strip()) > 3
        ]
    except Exception as e:
        print(f"[ERROR] LLM refinement failed: {e}")
        return raw_keywords  # Fallback