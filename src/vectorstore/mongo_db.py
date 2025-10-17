from typing import List

from langchain_core.stores import BaseStore
from pymongo import MongoClient
from langchain.schema import Document
import pickle

from pymongo.errors import ConnectionFailure
from pymongo.server_api import ServerApi

from config.vectorstore_config import MONGO_DATABASE
from utils.logger import setup_logger

logger = setup_logger(__name__)
class MongoDocstore(BaseStore):

    #def __init__(self, uri="mongodb://localhost:27017/",
    def __init__(self, uri=MONGO_DATABASE,
                 db_name="rag_db_mongo",
                 collection_name="parents_store"):
        try:
            self.client = MongoClient(uri, server_api=ServerApi('1'))
            # O comando ismaster verifica se a conexão foi bem-sucedida.
            self.client.admin.command('ismaster')
            logger.info("Conexão com o MongDB (Nuvem) estabelicida")
        except ConnectionFailure as e:
            logger.error(f"Erro ao conectar com MongoDB:\n {e}")

        self.collection = self.client[db_name][collection_name] #equivalente as tabelas

    def set(self, key: str, document: Document):
        """Salva um Document com um ID"""
        doc_dict = {"_id": key, "document": pickle.dumps(document)}
        self.collection.replace_one({"_id": key}, doc_dict, upsert=True)

    def get(self, key: str) -> Document | None:
        """Recupera um Document pelo ID"""
        result = self.collection.find_one({"_id": key})
        if result:
            return pickle.loads(result["document"])
        return None

    def _document_to_dict(self, document: Document) -> dict:
        """Converte um objeto Document para um dicionário para armazenamento."""
        return {"page_content": document.page_content, "metadata": document.metadata}

    def _dict_to_document(self, doc_dict: dict) -> Document:
        """Converte um dicionário do MongoDB de volta para um objeto Document."""
        return Document(page_content=doc_dict["page_content"], metadata=doc_dict["metadata"])

    def mset(self, items: list[tuple[str, Document]]):
        """Salvar múltiplos documentos de uma vez"""
        for key, document in items:
            doc_dict = {"_id": key, "document": self._document_to_dict(document)}
            self.collection.replace_one({"_id": key}, doc_dict, upsert=True)

    def mget(self, keys: list[str]):
        """Recupera múltiplos documentos pelo ID"""
        results = self.collection.find({"_id": {"$in": keys}})
        # docs = []
        # found_ids = set()
        # for r in results:
        #     docs.append(pickle.loads(r["document"]))
        #     found_ids.add(r["_id"])
        # return [next((d for d, r_id in zip(docs, found_ids) if r_id == k), None) for k in keys]
        found_docs = {r["_id"]: self._dict_to_document(r["document"]) for r in results}
        return [found_docs.get(key) for key in keys]

    def mdelete(self, keys: List[str]):
        """Deleta múltiplas chaves."""
        self.collection.delete_many({"_id": {"$in": keys}})

    def yield_keys(self):
        """Itera sobre todas as chaves do store."""
        for doc in self.collection.find({}, {"_id": 1}):
            yield doc["_id"]

    def clear(self):
        """Apaga todos os documentos da coleção"""
        result = self.collection.delete_many({})
        print(f"{result.deleted_count} documentos apagados.")