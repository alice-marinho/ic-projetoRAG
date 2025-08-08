import unittest
from rag.routing.router import get_router_decision
from rag.routing.routing_models import BuscaSimples, BuscaComposta

# esperado = "simples" ou "composta"
TEST_QUERIES = [
    ("Qual é a ementa da matéria 'Algoritmos' para o Técnico em Informática?", "simples"),
    ("Compare as disciplinas de IA e Ética", "composta"),
    ("Qual a diferença de carga horária entre 'Língua Portuguesa 1' e 'Matemática 1' no primeiro ano do Técnico em Informática?", "composta"),
    ("Fale mais sobre o conteúdo programático de 'História da Ciência e da Tecnologia' para o curso de ADS.", "simples"),
    ("Crie um projeto que una IA e Segurança da Informação", "composta"),
    ("Monte uma prova interdisciplinar para o Técnico em Informática, combinando os conceitos de 'Lógica de Programação' da matéria de Algoritmos com a 'Teoria dos Conjuntos' de Matemática 1.", "composta"),
    ("Gere uma atividade unindo os conhecimentos de 'Inglês Técnico Inicial' e 'Desenvolvimento Web'","composta"),
    ("Gere uma atividade de tradução técnica para a turma de ADS. A atividade deve usar um trecho da documentação de "
     "um framework JavaScript, unindo os conhecimentos de 'Inglês Técnico Inicial' e 'Desenvolvimento Web'",
     "composta"),
    ("Qual a diferença de carga horária entre 'Língua Portuguesa 1' e 'Matemática 1' no primeiro ano do Técnico em "
     "Informática?", "composta"),
    ("Qual é a ementa da matéria 'Algoritmos' para o Técnico em Informática?","simples"),
    ("Fale mais sobre o conteúdo programático de 'História da Ciência e da Tecnologia' para o curso de ADS.", "simples")
]

class TestRouterQueries(unittest.TestCase):

    def test_router_classification(self):
        for question, expected_type in TEST_QUERIES:
            with self.subTest(question=question):
                result = get_router_decision(question)
                if expected_type == "simples":
                    self.assertIsInstance(result, BuscaSimples, f"Falhou: {question}")
                else:
                    self.assertIsInstance(result, BuscaComposta, f"Falhou: {question}")

if __name__ == "__main__":
    unittest.main()
