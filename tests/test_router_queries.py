import pytest

from backend.src.rag.routing.router import get_router_decision

# esperado = "simples" ou "composta"
TEST_QUERIES = [
    ("Qual é a ementa da matéria 'Algoritmos' para o Técnico em Informática?", "BuscaSimples"),
    ("Compare as disciplinas de IA e Ética", "BuscaComposta"),
    ("Qual a diferença de carga horária entre 'Língua Portuguesa 1' e 'Matemática 1' no primeiro ano do Técnico em Informática?", "BuscaComposta"),
    ("Fale mais sobre o conteúdo programático de 'História da Ciência e da Tecnologia' para o curso de ADS.", "BuscaSimples"),
    ("Crie um projeto que una IA e Segurança da Informação", "BuscaComposta"),
    ("Monte uma prova interdisciplinar para o Técnico em Informática, combinando os conceitos de 'Lógica de Programação' "
     "da matéria de Algoritmos com a 'Teoria dos Conjuntos' de Matemática 1.", "BuscaComposta"),
    ("Gere uma atividade unindo os conhecimentos de 'Inglês Técnico Inicial' e 'Desenvolvimento Web'","BuscaComposta"),
    ("Gere uma atividade de tradução técnica para a turma de ADS. A atividade deve usar um trecho da documentação de "
     "um framework JavaScript, unindo os conhecimentos de 'Inglês Técnico Inicial' e 'Desenvolvimento Web'",
     "BuscaComposta"),
    ("Qual a diferença de carga horária entre 'Língua Portuguesa 1' e 'Matemática 1' no primeiro ano do Técnico em "
     "Informática?", "BuscaComposta"),
    ("Qual é a ementa da matéria 'Algoritmos' para o Técnico em Informática?","BuscaSimples"),
    ("Fale mais sobre o conteúdo programático de 'História da Ciência e da Tecnologia' para o curso de ADS.",
     "BuscaSimples"),
    ("Monte uma prova para o 1º ano do Técnico em Informática com questões que avaliem a capacidade de interpretação "
     "de texto de 'Língua Portuguesa 1' aplicada a problemas de lógica de programação da disciplina de 'Algoritmos'",
     "BuscaComposta"),
    ("Desenvolva um"
     " projeto de pesquisa para o 1º ano do Ensino Médio que conecte o conteúdo de História (com foco em Renascimento) e Arte",
     "BuscaComposta")
]

@pytest.mark.parametrize("question,expected_type", TEST_QUERIES)
def test_router_classification(question, expected_type):
    result = get_router_decision(question)
    assert result == expected_type, \
        f"Falhou: {question}, esperado {expected_type}, obtido {result}"

