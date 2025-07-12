import pandas as pd


class DataService:
    def __init__(self, caminho_csv: str):
        self.df = pd.read_csv(caminho_csv)

    def listar_cursos(self):
        return sorted(self.df["Curso"].dropna().unique().tolist())

    def listar_componentes(self, curso: str):
        df_filtrado = self.df[self.df["Curso"] == curso]
        return sorted(df_filtrado["Componente curricular"].unique().tolist())

    def listar_periodo(self, curso: str):
        df_filtrado = self.df[self.df["Curso"] == curso]
        return sorted(df_filtrado["Período Educacional"].unique().tolist())

    def filtrar_disciplinas(self, curso: str, componentes: list):
        resultado = self.df[
            (self.df["Curso"] == curso) &
            (self.df["Componente curricular"].isin(componentes))
            ]
        return resultado.reset_index(drop=True)

    def listar_componentes_por_curso_e_periodo(self, curso: str, periodo: str):
        df_filtrado = self.df[
            (self.df["Curso"] == curso) &
            (self.df["Período Educacional"] == periodo)
            ]
        return sorted(df_filtrado["Componente curricular"].dropna().unique().tolist())

