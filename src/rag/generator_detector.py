from rag import generate_response
from src.llm import LLMClient
from utils.logger import setup_logger

def responder_adaptativamente(question, context, history):
    tipo = IntentDetector.detectar_tipo_de_atividade(question)

    if tipo == "geral":
        return generate_response(question, context, history)

    if tipo == "projeto":
        prompt = ActivityGenerators.montar_prompt_projeto(question, context, history)
    elif tipo == "prova":
        prompt = ActivityGenerators.montar_prompt_prova(question, context, history)
    elif tipo == "atividade":
        prompt = ActivityGenerators.montar_prompt_atividade(question, context, history)
    else:
        prompt = ActivityGenerators.montar_prompt_geral(question, context, history)

    llm = LLMClient()
    return llm.chat(prompt)

class IntentDetector:
    @staticmethod
    def detectar_tipo_de_atividade(question: str) -> str:
        """
        Classifica a intenção da pergunta do professor.
        Retornos possíveis: 'projeto', 'prova', 'atividade', 'plano_aula', 'geral'
        """
        prompt = f"""
    Você é um classificador de intenção para um chatbot educacional.

    Analise a pergunta abaixo e classifique a intenção principal do professor.

    Pergunta: "{question}"

    Escolha apenas uma entre estas opções:
    - projeto
    - prova
    - atividade
    - plano_aula
    - geral

    Exemplos:
    "Monte uma prova interdisciplinar sobre lógica e matemática" → prova  
    "Crie um projeto entre algoritmos e matemática 1" → projeto  
    "Quero uma atividade prática de programação" → atividade  
    "Preciso de um plano de aula para ensinar variáveis" → plano_aula  
    "Qual o conteúdo de algoritmos?" → geral

    Atenção: se o termo 'prova' estiver presente, classifique como 'prova'.  
    O mesmo para 'projeto', 'atividade', 'plano de aula'.

    Responda apenas com a palavra correspondente.
    """
        llm = LLMClient()
        resposta = llm.chat(prompt).strip().lower()

        if any(palavra in question.lower() for palavra in ["prova", "teste", "avaliação"]):
            return "prova"
        elif any(palavra in question.lower() for palavra in ["projeto", "criar um projeto"]):
            return "projeto"
        elif any(palavra in question.lower() for palavra in ["atividade", "exercício"]):
            return "atividade"
        elif "plano de aula" in question.lower():
            return "plano_aula"

        return resposta if resposta in ["projeto", "prova", "atividade", "plano_aula"] else "geral"


class ActivityGenerators:
    @staticmethod
    def montar_prompt_projeto(question, context, history, max_history=5):
        context_text = "\n\n".join(context)
        ultimas_trocas = history[-max_history:] if history else []
        conversation_history = ""
        for troca in ultimas_trocas:
            conversation_history += f"Usuário: {troca['pergunta']}\nIA: {troca['resposta']}\n"

        return f""" 
Aja como um professor criativo e especialista em pedagogia interdisciplinar. Seu objetivo é ajudar outros educadores a criar projetos inovadores que conectem diferentes áreas do conhecimento.

Abaixo está o histórico da conversa até o momento entre o Humano e você (IA). Use-o para entender o contexto de perguntas de acompanhamento, mas não para responder à pergunta atual, a menos que seja explicitamente solicitado.
{conversation_history}

Abaixo estão os trechos de documentos relevantes. A resposta DEVE ser extraída ou sintetizada a partir destes trechos para embasar a criação do projeto.
{context}

### TEMA PROPOSTO PELO USUÁRIO 
{question}

### TAREFA PRINCIPAL E FORMATO DA RESPOSTA ###
Com base no TEMA PROPOSTO e nos DOCUMENTOS DE REFERÊNCIA, sua tarefa é elaborar uma proposta de projeto interdisciplinar. Siga rigorosamente a estrutura abaixo:

1.  **Parágrafo de Abertura:**  Reconheça o tema proposto pelo usuário e mostre entusiasmo pela ideia de conectar as disciplinas e introduza para ideia.

2.  **Título do Projeto:** Crie um título criativo e chamativo para o projeto.

3.  **Estrutura do Projeto:** Apresente as seguintes seções, usando os títulos em negrito:
    * **Introdução:** Apresente o projeto, explicando a relevância de conectar as disciplinas mencionadas no tema e como isso pode enriquecer o aprendizado dos alunos.
    * **Objetivos:** Liste com marcadores (bullet points) os principais objetivos de aprendizagem para os alunos, tanto da disciplina principal quanto da correlata.
    * **Metodologia:** Descreva o passo a passo de como a atividade seria conduzida. Sugira atividades práticas, pesquisas ou apresentações que os alunos fariam.
    * **Resultados Esperados:** Detalhe o que se espera que os alunos produzam ao final do projeto (ex: um seminário, um protótipo, um artigo, uma exposição de arte) e quais competências terão desenvolvido.

4.  **REGRA DE OURO:** Se os documentos de referência não fornecerem informações suficientes para criar uma proposta de projeto viável sobre o tema, informe de maneira educada que o material de apoio é insuficiente para detalhar a metodologia ou os objetivos, e peça mais informações ao usuário. NÃO invente detalhes que não possam ser sustentados pelo contexto.
    """

    @staticmethod
    def montar_prompt_prova(question, context, history, max_history=5):
        context_text = "\n\n".join(context)
        ultimas_trocas = history[-max_history:] if history else []
        conversation_history = ""
        for troca in ultimas_trocas:
            conversation_history += f"Usuário: {troca['pergunta']}\nIA: {troca['resposta']}\n"

        return f""" 
    Você é um assistente educacional. O professor solicitou uma prova.

    ===== CONTEXTO =====
    {context_text}
    ====================
    
    Histórico recente: {history}

    Solicitação: {question}

    Crie uma prova com:
    - Título
    - 10 questões (com dificuldade variada)
    - Coloque tanto manuscrita como multipla escolha
    - Gabarito unificado ao final da resposta
    - Separe as questões com um enter, deixe sempre de fácil visualização

    Finalize a resposta com uma pergunta curta, direta e simples, relacionada ao conteúdo respondido, que incentive o usuário a continuar a conversa. Evite sugestões muito longas ou complexas.
    """
    # Você é um professor que deseja realizar uma atividade conjunta com um professor de outra disciplina que tem assuntos correlatos

    @staticmethod
    def montar_prompt_atividade(question, context, history, max_history=5):
        context_text = "\n\n".join(context)
        ultimas_trocas = history[-max_history:] if history else []
        conversation_history = ""
        for troca in ultimas_trocas:
            conversation_history += f"Usuário: {troca['pergunta']}\nIA: {troca['resposta']}\n"

        return f""" 
    Você é um assistente educacional. O professor solicitou uma atividade didática.

    ===== CONTEXTO =====
    {context_text}
    ====================
    
    Histórico recente: {history}

    Solicitação: {question}

    Crie uma atividade com:
    - Objetivo
    - Instruções para os alunos
    - Descrição da tarefa
    - Critérios de avaliação
    - Materiais necessários

    Finalize com uma pergunta sugestiva, como: "Deseja transformar essa atividade em uma oficina prática?"
    """

    @staticmethod
    def montar_prompt_geral(question, context, history, max_history=5):
        context_text = "\n\n".join(context)
        ultimas_trocas = history[-max_history:] if history else []
        conversation_history = ""
        for troca in ultimas_trocas:
            conversation_history += f"Usuário: {troca['pergunta']}\nIA: {troca['resposta']}\n"

        return f""" 
    Você é um assistente educacional que responde com base no contexto abaixo.

    ===== CONTEXTO =====
    {context_text}
    ====================
    
    Histórico recente: {history}

    Solicitação: {question}
    
    Responda com clareza. Finalize com uma pergunta sugestiva para manter a conversa fluindo.
    """
