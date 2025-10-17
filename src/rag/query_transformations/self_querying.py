from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain_community.query_constructors.chroma import ChromaTranslator
from langchain_core.language_models import BaseChatModel
from langchain.prompts.prompt import PromptTemplate

from llm import LLMClient

structured_query_prompt = PromptTemplate(
    input_variables=["query"],
    template=(
        "Você é um assistente que recupera informações de disciplinas. "
        "Baseado na pergunta: '{query}', gere um filtro para buscar nos campos 'curso', 'componente', 'codigo' e 'periodo'. "
        "Priorize o componente que corresponde à disciplina mencionada na pergunta."
    )
)

class SelfQuery:
    def __init__(self):
        self.llm_client = LLMClient().llm

    def create_self_query_retriever(self ,vectorstore):
        metadata_field_info = [
            AttributeInfo(
                name="curso",
                description="O nome ou a sigla do curso de graduação ao qual a disciplina pertence. \
                Exemplos: 'Análise e Desenvolvimento de Sistemas', 'Ciência da Computação', 'ADS'",
                type="string"
            ),
            AttributeInfo(
                name="componente",
                description="O nome da disciplina, matéria ou componente curricular. Exemplo: 'Algoritmos', 'Língua Portuguesa 1'",
                type="string"
            ),
            AttributeInfo(
                name="periodo",
                description="APENAS o semestre ou ano letivo em que a disciplina é oferecida. Use este campo para "
                            "responder perguntas sobre 'em qual período', 'qual semestre' ou 'em que ano' uma "
                            "disciplina é ensinada. Ex: '1º semestre', '1 ano'.",
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


        document_content_description = ("Conteúdo programático, ementa, objetivos e informações detalhadas de uma disciplina ou matéria "
        "de cursos técnicos ou superiores. Inclui informações como habilidades desenvolvidas e tópicos abordados.")
        retriever = SelfQueryRetriever.from_llm(
                llm=self.llm_client,
                vectorstore=vectorstore,
                document_contents=document_content_description,
                metadata_field_info=metadata_field_info,
                structured_query_translator=ChromaTranslator(),
                structured_query_prompt=structured_query_prompt,
                verbose=True
            )

        return retriever
