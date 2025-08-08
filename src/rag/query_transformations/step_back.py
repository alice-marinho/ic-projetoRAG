from config.llm_config import LLM_MODEL, LLM_API_KEY
from langchain_together import ChatTogether


def gerar_resposta_final(original_question: str, context_list: list[str], conversation_history: list) -> str:
    """
    Gera a resposta final para o usuário usando a técnica de Step-Back Prompting.

    Args:
        original_question: A pergunta exata que o usuário fez.
        context_list: Uma lista de strings, onde cada string é um chunk de texto recuperado.
        conversation_history: O histórico da conversa para manter o contexto (opcional para esta etapa).

    Returns:
        A resposta final gerada pelo LLM.
    """
    print("[INFO] Montando o prompt final com a técnica Step-Back...")

    # combina os chunks de contexto em um único bloco de texto
    context_str = "\n\n---\n\n".join(context_list)

    # define o template do prompt.
    prompt_template = f"""
        Você é um assistente de IA especialista em pedagogia e elaboração de projetos acadêmicos. Sua tarefa é gerar respostas detalhadas e bem fundamentadas com base no contexto fornecido. Siga estritamente as duas etapas abaixo.
        
        ---------------------------------
        **CONTEXTO RECUPERADO DOS DOCUMENTOS:**
        {context_str}
        ---------------------------------
        **PERGUNTA ORIGINAL DO USUÁRIO:**
        "{original_question}"
        ---------------------------------
        
        **SUA TAREFA EM DUAS ETAPAS:**
        
        **Etapa 1 (O "Passo Atrás" - Step-Back):**
        Primeiro, analise o contexto e a pergunta para responder a esta questão de alto nível: Qual é o princípio pedagógico fundamental ou o conceito central que conecta os principais tópicos mencionados na pergunta do usuário?
        
        **Etapa 2 (A Geração da Resposta Detalhada):**
        Agora, usando o princípio que você identificou na Etapa 1 como sua linha de raciocínio principal, elabore uma resposta completa, rica e detalhada para a pergunta original do usuário. Organize a resposta de forma clara e use os detalhes específicos do contexto para embasar seus argumentos e sugestões.
        """

    llm_generator = ChatTogether(
        model=LLM_MODEL,
        temperature=0.1,
    )

    print("[INFO] Enviando prompt para o LLM Gerador...")
    response = llm_generator.invoke(prompt_template)

    # O objeto de resposta da LangChain geralmente tem o texto no atributo .content
    final_answer = response.content if hasattr(response, 'content') else str(response)

    return final_answer