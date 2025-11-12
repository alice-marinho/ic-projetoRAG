# Em scripts/create_admin.py
import sys
import os

# Adiciona a raiz do projeto ao path do Python para encontrar os módulos
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from database.database import SessionLocal
from database.models import UserRole
from auth.user_service import get_user_by_email, create_user


def main():
    """
    Script de linha de comando para criar um Super Admin JÁ ATIVO.
    """
    print("--- Utilitário de Criação de Super Admin ---")

    db = SessionLocal()
    try:
        email = input("Email do Super Admin: ").strip()
        if not email:
            print("Email não pode ser vazio.")
            return

        if get_user_by_email(email, db):
            print("Erro: Usuário com este email já existe.")
            return

        password = input("Senha do Super Admin: ")
        if not password:
            print("Senha não pode ser vazia.")
            return

        # Chama a função de backend
        create_user(
            db=db,
            name="Super Admin",
            email=email,
            plain_password=password,
            role=UserRole.super_admin,
            is_active=True  # <-- Super Admins criados por script já são ATIVOS
        )

        print(f"\n[SUCESSO] Usuário Super Admin '{email}' criado com sucesso!")

    except Exception as e:
        print(f"\n[ERRO] Falha ao criar admin: {e}")
    finally:
        db.close()
        print("--- Conexão com banco fechada ---")


if __name__ == "__main__":
    main()