

"""
    Classe aplica a interdisiciplinaridade

    :param curso
    :param periodo educacional
    :param disciplina 1
    :param disciplina 2

    :return


"""
from llm import LLMClient
from vectorstore import VectorStoreManager


class Interdisciplina:
    def __init__(
            self,
            curso:str,
            periodo:str,
            disciplinas: list[str]
           # disciplina2: str
    ):
        self.curso = curso
        self.periodo = periodo
        self.disciplinas = disciplinas
        self.vectorstore = VectorStoreManager()

       # self.disciplina2 = disciplina2

    def executar(self):
        print(f"🔍 Buscando chunks para:\nCurso: {self.curso}\nPeríodo: {self.periodo}\nDisciplinas: {self.disciplinas}")
        chunks_gerais = []

        for comp in self.disciplinas:
            # ✅ Busca textual no conteúdo, sem filtro de metadados
            docs = self.vectorstore.buscar_chunks_por_texto(
                texto_busca=comp,
                k=10
            )

            if docs:
                texto = "\n".join([doc.page_content for doc in docs])
                chunks_gerais.append((comp, texto))
            else:
                print(f"❌ Nenhum chunk encontrado para: {comp}")

        if len(chunks_gerais) < 2:
            print("⚠️ É necessário pelo menos duas disciplinas com conteúdo disponível.")
            return

        print("\n💬 Enviando para a IA...")
        # Aqui você pode continuar com a lógica de geração ou sugestão com IA usando `chunks_gerais`

    # def executar(self):
    #     print(f"🔍 Buscando chunks para:\nCurso: {self.curso}\nPeríodo: {self.periodo}\nDisciplinas: {self.disciplinas}")
    #     chunks_gerais = []
    #
    #     for comp in self.disciplinas:
    #         docs = self.vectorstore.buscar_chunks_por_metadados(
    #             curso=self.curso,
    #             periodo=self.periodo,
    #             componente=comp,
    #             k=10
    #         )
    #         if docs:
    #             texto = "\n".join([doc.page_content for doc in docs])
    #             chunks_gerais.append((comp, texto))
    #         else:
    #             print(f"❌ Nenhum chunk encontrado para: {comp}")
    #
    #     if len(chunks_gerais) < 2:
    #         print("⚠️ É necessário pelo menos duas disciplinas com conteúdo disponível.")
    #         return
    #
    #     print("\n💬 Enviando para a IA...")
    #
    #     prompt = "Com base nos conteúdos apresentados abaixo, gere sugestões de projetos interdisciplinares contextualizados:\n\n"
    #     for comp, texto in chunks_gerais:
    #         prompt += f"\n\n---\n📘 {comp}:\n{texto}"
    #
    #     resposta = LLMClient().chat(prompt)
    #     print("\n🧠 Resposta da IA:\n")
    #     print(resposta)

    def interdisciplinaridade_filtros(self) -> str:
        """
        Busca os chunks das disciplinas no CSV e gera uma proposta interdisciplinar com a LLM.
        """
        dados = self.chunk_service.filtrar_conteudo(
            curso=self.curso,
            periodo=self.periodo,
            componentes=self.disciplinas
        )

        if len(dados) < 2:
            return "⚠️ É necessário pelo menos duas disciplinas com conteúdo disponível."

        textos = []
        for item in dados:
            nome = item.get("Componente curricular", "Sem nome")
            ementa = item.get("Ementa", "")
            objetivos = item.get("Objetivos", "")
            conteudo = item.get("Conteúdo Programático", "")

            texto_unico = f"Ementa: {ementa}\nObjetivos: {objetivos}\nConteúdo: {conteudo}"
            textos.append((nome, texto_unico))

        # Monta prompt
        prompt = f"Curso: {self.curso} | Período: {self.periodo}\n\n"
        for nome, conteudo in textos:
            prompt += f"--- {nome} ---\n{conteudo}\n\n"

        prompt += "Com base nesses conteúdos, proponha ideias de projetos e atividades interdisciplinares contextualizadas."

        print("\n💬 Enviando para a IA...")
        resposta = LLMClient().chat(prompt)
        return resposta
