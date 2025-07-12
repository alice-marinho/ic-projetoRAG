import pandas as pd

from llm import LLMClient
from rag import retrieve_context
from searcher.course_service import DataService
from config.config import CLEAN_CSV

class AppController:
    def __init__(self, caminho_csv=CLEAN_CSV):
        self.curso = None
        self.semestre = None
        self.componentes = None
        self.service = DataService(caminho_csv)

    def executar(self):
        self._mostrar_cursos()
        self.curso = self._selecionar_curso()
        self.semestre = self._selecionar_semestre(self.curso)
        self.componentes = self._selecionar_componentes(self.curso, self.semestre)
        # self._enviar_llm(self.curso, self.semestre, self.componente)



    def _mostrar_cursos(self):
        print("Cursos disponíveis:")
        for i, curso in enumerate(self.service.listar_cursos()):
            print(f"{i+1}. {curso}")

    def _selecionar_curso(self):
        cursos = self.service.listar_cursos()
        while True:
            try:
                idx = int(input("Digite o número do curso desejado: ")) - 1
                if 0 <= idx < len(cursos):
                    return cursos[idx]
                else:
                    print("Número inválido. Tente novamente.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

    def _selecionar_semestre(self, curso):
        semestres = self.service.listar_periodo(curso)
        print("\nSemestres disponíveis:")
        for i, semestre in enumerate(semestres):
            print(f"{i+1}. {semestre}")
        while True:
            try:
                idx = int(input("Digite o número do semestre desejado: ")) - 1
                if 0 <= idx < len(semestres):
                    return semestres[idx]
                else:
                    print("Número inválido. Tente novamente.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

    def _selecionar_componentes(self, curso, semestre):
        componentes = self.service.listar_componentes_por_curso_e_periodo(curso, semestre)
        print("\nComponentes disponíveis:")
        for i, comp in enumerate(componentes):
            print(f"{i + 1}. {comp}")

        while True:
            indices = input("Digite os números dos componentes (mínimo 2), separados por vírgula: ")
            try:
                selecionados = [componentes[int(i.strip()) - 1] for i in indices.split(",")]
                if len(selecionados) < 2:
                    print("⚠️ Você deve selecionar pelo menos 2 componentes.")
                    continue
                return selecionados
            except (ValueError, IndexError):
                print("❌ Entrada inválida. Tente novamente com números válidos.")

    def _enviar_llm(self, curso: str, semestre: str, componentes: list) -> str | list[dict]:
        """
        1. Filtra os dados com base na seleção do usuário.
        2. Converte em um formato que o retriever possa buscar.
        3. Chama o retriever e o LLM.
        """
        # Passo 1: Filtra os dados do DataFrame
        dados_filtrados = self.service.df[
            (self.service.df["Curso"] == curso) &
            (self.service.df["Período Educacional"] == semestre) &
            (self.service.df["Componente curricular"].isin(componentes))
            ]

        if dados_filtrados.empty:
            return "Nenhum dado encontrado para os critérios selecionados."

        # Passo 2: Formata os dados para o retriever (exemplo: concatenar campos relevantes)
        contexto = self._formatar_para_retriever(dados_filtrados)

        # Passo 3: Busca no banco vetorial (usando o texto formatado como query)
        resultados = retrieve_context(contexto, 1)  # Chama sua função existente
        print(f"\n[DEBUG DEPOIS] Resultados obtidos (TIPO): {type(resultados)}")
        print(f"\n\n[DEBUG CONTEÚDO] {resultados}")
        return resultados
        # Passo 4: Gera a resposta com o LLM
        # prompt = f"""
        # Com base nos dados abaixo, gere uma resposta sobre o curso {curso}, semestre {semestre} e componentes {componentes}:
        # Contexto: {resultados}
        # """
        # return LLMClient().chat(prompt)

    @staticmethod
    def _formatar_para_retriever(dados: pd.DataFrame) -> str:
        """
        Converte o DataFrame filtrado em um texto otimizado para busca no retriever.
        Exemplo: concatena 'Curso', 'Período' e 'Componente curricular'.
        """
        textos = []
        for _, row in dados.iterrows():
            texto = f"""
            Curso: {row['Curso']}
            Período: {row['Período Educacional']}
            Componente: {row['Componente curricular']}
            Descrição: {row.get('Descrição', 'Não informado')}
            """
            textos.append(texto)
        return "\n".join(textos)