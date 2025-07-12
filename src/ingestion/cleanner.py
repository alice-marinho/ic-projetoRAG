import json
import re

import pandas as pd

from config import config
from config.config import *
from utils.logger import *

logger = setup_logger(__name__)


class TextCleaner:
    def __init__(
            self,
            clean_data_file=config.CLEAN_DATA_FILE
    ):
        self.clean_data_file = clean_data_file

    @staticmethod
    def _padronizar_nome_curso(nome: str) -> str:
        """
        Padroniza nomes de cursos para evitar duplicações.
        Exemplo:
            - "Superior de Bacharelado em Turismo" → "Bacharelado em Turismo"
        """
        if not isinstance(nome, str):
            return nome

        nome = nome.strip().upper()

        # Regras de substituição (ajuste conforme seus dados)
        padroes = [
            (r"SUPERIOR DE BACHARELADO EM", "BACHARELADO EM"),
            (r"SUPERIOR DE TECNOLOGIA EM", "TECNÓLOGO EM"),
            (r"TECNOLOGIA EM", "TECNÓLOGO EM"),
            (r"TÉCNICO EM", "TÉCNICO EM"),
        ]

        for padrao, substituicao in padroes:
            nome = re.sub(padrao, substituicao, nome, flags=re.IGNORECASE)

        return nome.strip().title()

    @staticmethod
    def _clean_text(texto):
        """
        Limpa texto de campos multilinha para melhorar embedding.
        """
        if not texto:
            return texto

        texto = re.sub(r'(?i)Projeto Pedagógico do Curso.*?\n', '', texto)
        texto = re.sub(r'(?i)Tecnologia em .*?\n', '', texto)
        texto = re.sub(r'\n\s*\d+\s*\n', '\n', texto)
        texto = re.sub(r'\n\s*CUBATÃO\s*\n', '\n', texto, flags=re.IGNORECASE)
        texto = re.sub(r'\nC[ÂA]MPUS\s*CUBATÃO\s*\n', '\n', texto, flags=re.IGNORECASE)
        texto = re.sub(r'\n\s*TÉCNICO EM [A-ZÀ-Ú ]+\s*\n', '\n', texto, flags=re.IGNORECASE)
        texto = re.sub(r'\n+', '\n', texto)
        texto = re.sub(r'[ \t]+', ' ', texto)
        texto = texto.replace('\n', ' ')
        texto = texto.strip()

        return texto

    @staticmethod
    def clean_save_json(text: list, output_path: Path = CLEAN_DATA_FILE) -> list:
        """
        Aplica limpeza usando pandas e salva os dados em JSON e CSV.
        """
        logger.info("Iniciando limpeza com pandas...")

        try:
            # Converte para DataFrame
            df = pd.DataFrame(text)

            if "Curso" in df.columns:
                df["Curso"] = df["Curso"].apply(TextCleaner._padronizar_nome_curso)

            # Cria coluna "Período Educacional" para unificar
            df["Período Educacional"] = df.apply(TextCleaner._format_periodo, axis=1)

            # Remove colunas ano e semestre
            df.drop(columns=["Ano", "Semestre"], inplace=True, errors='ignore')

            # Substitui valores nulos e vazios por "Não informado"
            df.replace(r'^\s*$', pd.NA, regex=True, inplace=True)
            df.replace("N/A", pd.NA, inplace=True)
            df.fillna("Não informado", inplace=True)

            # Aplica limpeza de texto em campos multilinha
            for field in MULTILINE_FIELDS:
                if field in df.columns:
                    df[field] = df[field].astype(str).apply(TextCleaner._clean_text)
                    df[field] = df[field].replace({pd.NA: "Não informado", "nan": "Não informado"}).fillna(
                        "Não informado")

            # Campos numéricos (WORKLOAD): preencher com 0
            for field in WORKLOAD:
                if field in df.columns:
                    df[field] = (
                        df[field]
                        .astype(str)
                        .str.replace(",", ".", regex=False)
                        .str.strip(" .")
                    )
                    df[field] = pd.to_numeric(df[field], errors="coerce").fillna("0").astype(str)

            # Para os demais campos: preenche com "Não informado" onde for nulo
            for col in df.columns:
                if col not in MULTILINE_FIELDS and col not in WORKLOAD:
                    df[col] = df[col].fillna("Não informado")

                    # Tira os pontos finais
                    df[col] = df[col].astype(str).apply(lambda x: re.sub(r'\.\s*$', '', x.strip()))

            df = TextCleaner._sum_workload_columns(df)

            # Exporta para JSON limpo
            df.to_json(output_path, orient="records", indent=2, force_ascii=False)
            logger.info(f"JSON limpo salvo: {output_path}")

            # Exporta para CSV
            df.to_csv(CLEAN_CSV, index=False, encoding="utf-8-sig")
            logger.info("CSV salvo com sucesso.")

            return df.to_dict(orient="records")

        except Exception as e:
            logger.error(f"Erro ao processar dados com pandas: {e}")
            raise

    """
    Aqui ele formata o período para uma nova coluna "Período Educacional"
    """
    @staticmethod
    def _format_periodo(item_json: dict)-> str:
        ano = item_json.get("Ano") or item_json.get("ano")
        semestre = item_json.get("Semestre") or item_json.get("semestre")

        ano = str(ano).strip() if ano is not None else ""
        semestre = str(semestre).strip() if semestre is not None else ""

        if ano:
            return f"{ano}º Ano"
        elif semestre:
            return f"{semestre}º Semestre"
        else:
            return "Não informado"

    @staticmethod
    def _sum_workload_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Soma as colunas de carga horária e cria a coluna 'Carga Horária Total'.
        """
        workload_cols = [col for col in WORKLOAD if col in df.columns]

        if not workload_cols:
            logger.info("Nenhuma coluna de carga horária encontrada para somar.")
            df['Carga Horária Total'] = 0
            return df

        for col in workload_cols:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .str.strip(" .")
            )
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['Carga Horária Total'] = df[workload_cols].sum(axis=1).astype(int)
        df.drop(columns=workload_cols, inplace=True)
        logger.info(f"Coluna 'Carga Horária Total' criada e colunas {workload_cols} removidas.")

        return df
