import argparse
import getpass
import sqlite3

from werkzeug.security import generate_password_hash

from db import init_db, DB_PATH


def ensure_db():
    init_db()


def create_user(username: str, email: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                 (username, email, generate_password_hash(password)))
    conn.commit()
    conn.close()
    print(f"[create_admin] Usuário criado: {username} ({email})")


def main():
    parser = argparse.ArgumentParser(description="Criar usuário inicial no banco.")
    parser.add_argument("--username", required=True, help="Nome de usuário (login)")
    parser.add_argument("--email", required=True, help="Email do usuário")
    parser.add_argument("--password", help="Senha (se omitido, será solicitada)")
    args = parser.parse_args()

    pwd = args.password or getpass.getpass("Senha: ")
    ensure_db()
    create_user(args.username, args.email, pwd)


if __name__ == "__main__":
    main()
