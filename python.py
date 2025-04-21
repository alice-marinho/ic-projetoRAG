import requests

MODEL = "phi"  # ou outro modelo que você tiver baixado
OLLAMA_URL = "http://localhost:11434/api/generate"

def perguntar_ollama(pergunta):
    payload = {
        "model": "phi",
        "prompt": pergunta,
        "stream": False
    }

    resposta = requests.post(OLLAMA_URL, json=payload)

    if resposta.status_code == 200:
        conteudo = resposta.json()
        return conteudo.get("response", "").strip()
    else:
        return f"Erro: {resposta.status_code} - {resposta.text}"

# Teste
resposta = perguntar_ollama("Explique de forma simples o que é aprendizado de máquina.")
print(resposta)
