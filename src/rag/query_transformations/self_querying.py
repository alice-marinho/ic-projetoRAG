from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain_community.query_constructors.chroma import ChromaTranslator
from langchain_together import ChatTogether

from config.llm_config import LLM_MODEL
from llm import LLMClient


def create_self_query_retriever(vectorstore):
    metadata_field_info = [
        AttributeInfo(
            name="curso",
            description="O nome ou a sigla do curso de graduação ao qual a disciplina pertence. \
            Exemplos: 'Análise e Desenvolvimento de Sistemas', 'Ciência da Computação', 'ADS'e",
            type="string or list[string]"
        ),
        AttributeInfo(
            name="componente_curricular",
            description="O nome oficial da disciplina, matéria ou componente curricular. \
            Exemplos: 'Programação de Computadores 1', 'Cálculo I', 'Desenvolvimento Web'",
            type="string or list[string]"
        ),
        AttributeInfo(
            name="periodo",
            description="APENAS o semestre ou ano letivo em que a disciplina é oferecida. Use este campo para "
                        "responder perguntas sobre 'em qual período', 'qual semestre' ou 'em que ano' uma "
                        "disciplina é ensinada. Ex: '1º período', '3', '1º ano'.",
            type="string or list[string]"
        ),
        # AttributeInfo(
        #     name="tipo",
        #     description="Classificação da disciplina quanto à obrigatoriedade",
        #     type="string or list[string]"
        # ),
        AttributeInfo(
            name="codigo",
            description="O código único e alfanumérico da disciplina. Exemplo: 'CC101', 'MAT203'",
            type="string or list[string]"
        )
    ]

    llm = ChatTogether(
        model=LLM_MODEL,
        temperature= 0
    )
    document_content_description = ("""IMPORTANTE: Sua tarefa é construir uma consulta de busca. NUNCA invente, 
                                    adivinhe ou presuma o valor de um filtro.Se a pergunta do usuário for "
                                    'qual o período...?', sua função é criar filtros para ENCONTRAR o documento relevante,
                                    e NÃO adivinhar a resposta e colocá-la no filtro. O conteúdo do documento 
                                    descreve a ementa, objetivos e competências de uma disciplina. 
                                    """)
    retriever = SelfQueryRetriever.from_llm(
            llm=llm,
            vectorstore=vectorstore,
            document_contents=document_content_description,
            metadata_field_info=metadata_field_info,
            # structured_query_translator=ChromaTranslator(),
            verbose=True
        )

    return retriever
