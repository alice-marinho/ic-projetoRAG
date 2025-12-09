import json
import pytest

from backend.src.process_question import ProcessQuestion
from backend.src.rag import RAGRetriever
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "json" / "test_retriever_data.json"
process = ProcessQuestion()

SIMPLE_CASES = [
    {
        "question": "Qual é a ementa da matéria Algoritmos?",
        "expected_course": "Técnico Em Informática Integrado Ao Ensino Médio",
        "expected_subject": "Algoritmos"
    },
    {
        "question": "Quais são os objetivos da disciplina Turismo e Hospitalidade?",
        "expected_course": "Bacharelado Em Turismo",
        "expected_subject": "Turismo e Hospitalidade"
    }
]

COMPOSITE_CASES = [
    {
        "question": "Explique os conteúdos de Algoritmos e Desenvolvimento Web",
        "expected_courses": ["Técnico Em Informática Integrado Ao Ensino Médio", "Tecnólogo Em Análise E Desenvolvimento De Sistemas"],
        "expected_subjects": ["Algoritmos", "Desenvolvimento Web"]
    }
]

with open(DATA_FILE, "r", encoding="utf-8") as f:
    TEST_DATA = json.load(f)


retriever = RAGRetriever()

@pytest.mark.parametrize("case", TEST_DATA)
def test_retriever_final_context(case):

    query = case["query"]
    # query = rewrite_query(query)


    expected_course = case["expected_course"]
    expected_subject = case["expected_subject"]

    docs = retriever.retriever_final_context(query, k=30)
    # print(len(docs))

    retrieved_courses = [doc.metadata.get("curso", "") for doc in docs]
    retrieved_componentes = [doc.metadata.get("componente", "") for doc in docs]

    print(query)
    assert expected_course in retrieved_courses, f"Esperava {expected_course}, mas retornou {retrieved_courses}"
    assert expected_subject in retrieved_componentes, f"Esperava {expected_subject}, mas retornou {retrieved_componentes}"

@pytest.mark.parametrize("case", SIMPLE_CASES)
def test_busca_simples_retriever(case):
    process.process_user_question(case["question"], conversation_history=[])
    docs = retriever.retriever_final_context(case["question"])

    retrieved_courses = [doc.metadata.get("curso", "") for doc in docs]
    retrieved_subjects = [doc.metadata.get("componente", "") for doc in docs]

    assert case["expected_course"] in retrieved_courses, f"Esperava {case['expected_course']}, mas retornou {retrieved_courses}"
    assert case["expected_subject"] in retrieved_subjects, f"Esperava {case['expected_subject']}, mas retornou {retrieved_subjects}"

@pytest.mark.parametrize("case", COMPOSITE_CASES)
def test_busca_composta_retriever(case):
    response = process.process_user_question(case["question"], conversation_history=[])
