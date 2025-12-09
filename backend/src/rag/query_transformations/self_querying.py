from langchain.chains.constitutional_ai.prompts import examples
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain_community.query_constructors.chroma import ChromaTranslator
from langchain_core.language_models import BaseChatModel
from langchain.prompts.prompt import PromptTemplate

from backend.src.llm import LLMClient

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
        # self.llm_client = LLMClient().llm
        pass

    @staticmethod
    def create_self_query_retriever(vectorstore, llm: BaseChatModel):
        metadata_field_info = [
            AttributeInfo(
                name="curso",
                description="O nome do curso de graduação ao qual a disciplina pertence. \
                Exemplos: 'Análise e Desenvolvimento de Sistemas', 'Ciência da Computação', 'ADS'. filter=Comparison(comparator='like', attribute='curso', value='Informática')",
                type="string"
            ),
            AttributeInfo(
                name="componente",
                description="O nome da disciplina, matéria ou componente curricular. EXEMPLO: 'Algoritmos', "
                            "'Língua Portuguesa 1'Me fale sobre Língua Portuguesa e Algoritmos,"
                    "filter=Operation(operator='or', arguments=[Comparison(comparator='like', attribute='componente', "
                            "value='Língua Portuguesa 1'), Comparison(comparator='eq', attribute='componente', value='Algoritmos')])"
                            "IMPORTANTE: Você DEVE usar uma busca 'contém' (like) para este campo, "
                            "já que os nomes reais podem ser mais longos (ex: 'Algoritmos' deve encontrar 'Algoritmos de Programação').",
                type="list[string]"
            ),
            AttributeInfo(
                name="periodo",
                description="O semestre ou ano letivo da disciplina. Use este campo para filtrar por períodos "
                            "específicos, Ex: 1º semestre', '1º ano', 'primeiro ano' = 1° ano",
                type="string"
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
                llm=llm,
                vectorstore=vectorstore,
                document_contents=document_content_description,
                metadata_field_info=metadata_field_info,
                #structured_query_prompt=structured_query_prompt,
                verbose=True,
                max_retries=3,
                retry_backoff_factor=2
            )

        return retriever


# from vectorstore import VectorStoreManager
#
# vectordb = VectorStoreManager()
# vectorstore = vectordb.load_vectorstore()
#
# SelfQuery().create_self_query_retriever(vectorstore)
#
# from langchain_postgres import PGVector
# from database.db_config import DATABASE_URL
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from config.vectorstore_config import EMBEDDING_SENTENCE_MODEL
#
#
# embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_SENTENCE_MODEL)
# llm = LLMClient().llm
# vectorstore = PGVector(
#             connection=DATABASE_URL,
#             embeddings=embeddings,
#             collection_name="child_chunks",
#             use_jsonb=True        )
#
# question = "Quais são os principais tópicos abordados no estudo das civilizações antigas em História?"
# retriever = SelfQuery().create_self_query_retriever(vectorstore, llm)
#
# child_chunks = retriever.invoke(question)
#
# print(f"{len(child_chunks)} chunks encontrados")
# for c in child_chunks:
#     print(c.page_content[:200], c.metadata)
