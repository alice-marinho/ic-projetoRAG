import hashlib
import json
import os
from pathlib import Path
from config import config


class DocsHashChecker:
    def __init__(
        self,
        docs_dir=config.DOCS_DIR,
        hash_file=config.HASH_FILE,
        algo="sha256"
    ):
        self.docs_dir = docs_dir
        self.hash_file = hash_file
        self.algo = algo

    def _get_hash_function(self):
        return hashlib.new(self.algo)

    def calculate_file_hash(self, file_path):
        """
        Calcula um hash robusto para um arquivo, incluindo conteúdo e metadados.
        """
        hash_func = self._get_hash_function()
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):
                hash_func.update(chunk)

        # Inclui metadados no hash (tamanho e data de modificação)
        stat = os.stat(file_path)
        hash_func.update(str(stat.st_mtime).encode())
        hash_func.update(str(stat.st_size).encode())

        return hash_func.hexdigest()

    def calculate_all_hashes(self):
        hashes = {}
        for file in sorted(self.docs_dir.rglob("*")):
            if file.is_file():
                relative_path = str(file.relative_to(self.docs_dir))
                hashes[relative_path] = self.calculate_file_hash(file)
        return hashes

    def get_changes(self) -> dict[str, list[str]]:
        """
        Compara os hashes atuais com os salvos e retorna um dicionário detalhado
        de mudanças.

        Returns:
            dict: Um dicionário com três chaves: 'added', 'removed', 'modified'.
                  Cada chave contém uma lista de caminhos de arquivo relativos.
        """
        current_hashes = self.calculate_all_hashes()

        if not self.hash_file.exists():
            # Se o arquivo de hash não existe, todos os arquivos são 'added'
            return {
                "added": list(current_hashes.keys()),
                "removed": [],
                "modified": []
            }

        with open(self.hash_file, "r") as f:
            saved_data = json.load(f)
            # Acessa a chave "file_hashes" que você definiu na sua estrutura
            saved_hashes = saved_data.get("file_hashes", {})

        current_files = set(current_hashes.keys())
        saved_files = set(saved_hashes.keys())

        added = list(current_files - saved_files)
        removed = list(saved_files - current_files)

        modified = []
        # Verifica arquivos que podem ter sido modificados (presentes em ambos os estados)
        potential_modified = current_files.intersection(saved_files)
        for file in potential_modified:
            if current_hashes[file] != saved_hashes.get(file):
                modified.append(file)

        return {"added": added, "removed": removed, "modified": modified}

    def save_current_hashes(self):
        """
        Calcula os hashes dos arquivos atuais no diretório e os salva no
        arquivo de hash. Deve ser chamado após o processamento bem-sucedido.
        """
        current_hashes = self.calculate_all_hashes()
        data = {"file_hashes": current_hashes}

        self.hash_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.hash_file, "w") as f:
            json.dump(data, f, indent=4)

    # def has_docs_changed(self):
    #     current_hashes = self.calculate_all_hashes()
    #
    #     if self.hash_file.exists():
    #         with open(self.hash_file, "r") as f:
    #             saved_hashes = json.load(f).get("file_hashes", {})
    #         if saved_hashes == current_hashes:
    #             return False  # Nenhuma alteração
    #
    #     self.save_hashes(current_hashes)
    #     return True  # Houve alteração
    #
    # def save_hashes(self, hashes):
    #     data = {"file_hashes": hashes}
    #     self.hash_file.parent.mkdir(parents=True, exist_ok=True)
    #     with open(self.hash_file, "w") as f:
    #         json.dump(data, f, indent=4)
