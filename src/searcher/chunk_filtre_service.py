# searcher/chunk_filter_service.py
import pandas as pd

class ChunkFilterService:
    def __init__(self, caminho_csv: str):
        self.df = pd.read_csv(caminho_csv)

    def filtrar_conteudo(self, curso: str, periodo: str, componentes: list[str]) -> list[dict]:
        resultado = self.df[
            (self.df["Curso"] == curso) &
            (self.df["Período Educacional"] == periodo) &
            (self.df["Componente curricular"].isin(componentes))
        ]
        return resultado.to_dict(orient="records")
