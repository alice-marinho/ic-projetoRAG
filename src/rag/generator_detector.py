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
    Você é um assistente educacional. O professor solicitou um projeto.

    ===== CONTEXTO =====
    {context_text}
    ====================
    
    Histórico recente: {history}

    Solicitação: {question}

    Crie um projeto pedagógico com a estrutura:
    1. Introdução
    2. Objetivo Geral
    3. Objetivos Específicos
    4. Metodologia
    5. Resultados Esperados
    6. Avaliação

    Finalize com uma pergunta sugestiva, como: "Deseja transformar isso em um plano de aula?"
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
