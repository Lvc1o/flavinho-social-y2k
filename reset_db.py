import os
import argparse
from pathlib import Path

from db import init_db, DB_PATH


def reset_db():
    db_path = Path(DB_PATH)
    if db_path.exists():
        db_path.unlink()
        print(f"[reset_db] Removido arquivo {db_path}")
    else:
        print(f"[reset_db] Arquivo {db_path} não existia.")
    init_db()
    print(f"[reset_db] Banco recriado em {db_path}")


def main():
    parser = argparse.ArgumentParser(description="Resetar o banco SQLite do projeto.")
    parser.add_argument("--yes", action="store_true", help="Confirma a remoção sem perguntar")
    args = parser.parse_args()

    if not args.yes:
        confirm = input("Tem certeza que deseja apagar e recriar o banco? (yes/no) ")
        if confirm.strip().lower() != "yes":
            print("Cancelado.")
            return
    reset_db()


if __name__ == "__main__":
    main()
