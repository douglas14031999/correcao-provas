"""
Script de Migração dos Dados Base do SQLite para o PostgreSQL.
Migra exclusivamente os dados operacionais essenciais (usuários e configurações do sistema/município)
sem levar provas e correções de teste, preparando o banco limpo para produção.

Uso:
    python backend/scripts/migrate_sqlite_to_postgres.py
    python backend/scripts/migrate_sqlite_to_postgres.py --with-schools   # Inclui também escolas, turmas e alunos
    python backend/scripts/migrate_sqlite_to_postgres.py --all            # Inclui todo o histórico (provas e submissões)
"""

import os
import sys
import argparse
import sqlite3

# Adicionar diretório raiz do backend ao sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Carregar variáveis de ambiente do .env se existir
try:
    from dotenv import load_dotenv
    env_file = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.exists(env_file):
        env_file = os.path.join(BACKEND_DIR, ".env")
    load_dotenv(env_file)
except ImportError:
    pass

import psycopg2
import psycopg2.extras

SQLITE_PATH = os.path.join(BACKEND_DIR, "storage", "exams.db")

def get_pg_connection(pg_url: str):
    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(pg_url)

def migrate_table(sqlite_conn, pg_conn, table_name: str, pkey: str, columns: list):
    s_cur = sqlite_conn.cursor()
    p_cur = pg_conn.cursor()

    col_str = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))

    s_cur.execute(f"SELECT {col_str} FROM {table_name}")
    rows = s_cur.fetchall()
    if not rows:
        print(f"  [i] Tabela '{table_name}' está vazia no SQLite. Nenhuma linha transferida.")
        return 0

    inserted = 0
    updated = 0

    update_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in columns if c != pkey])

    for row in rows:
        sql = f"""
            INSERT INTO {table_name} ({col_str})
            VALUES ({placeholders})
            ON CONFLICT ({pkey}) DO UPDATE SET {update_clause}
        """
        p_cur.execute(sql, row)
        inserted += 1

    pg_conn.commit()
    print(f"  [OK] Tabela '{table_name}': {inserted} registro(s) sincronizado(s) com sucesso.")
    return inserted

def main():
    parser = argparse.ArgumentParser(description="Migração de Dados Base (SQLite -> PostgreSQL)")
    parser.add_argument("--url", default=os.getenv("DATABASE_URL", ""), help="URL de conexão do PostgreSQL")
    parser.add_argument("--sqlite", default=SQLITE_PATH, help="Caminho do arquivo SQLite de origem")
    parser.add_argument("--with-schools", action="store_true", help="Migrar também escolas, turmas e alunos")
    parser.add_argument("--all", action="store_true", help="Migrar também provas e submissões")
    args = parser.parse_args()

    pg_url = (args.url or "").strip()
    if not pg_url:
        print("\n[ERRO] DATABASE_URL do PostgreSQL não foi informada!")
        print("Defina a variável de ambiente DATABASE_URL no seu .env ou passe via parâmetro:")
        print("  python backend/scripts/migrate_sqlite_to_postgres.py --url postgresql://user:senha@host:5432/nome_banco\n")
        sys.exit(1)

    if not os.path.exists(args.sqlite):
        print(f"\n[ERRO] Arquivo SQLite não encontrado em: {args.sqlite}\n")
        sys.exit(1)

    print("\n" + "="*70)
    print("  MIGRAÇÃO DE DADOS BASE: SQLITE -> POSTGRESQL")
    print("="*70)
    print(f"Origem SQLite:     {args.sqlite}")
    print(f"Destino Postgres:  {pg_url.split('@')[-1] if '@' in pg_url else 'PostgreSQL'}")
    print("="*70)

    # Conectar ao SQLite
    s_conn = sqlite3.connect(args.sqlite)

    # Conectar ao PostgreSQL
    try:
        p_conn = get_pg_connection(pg_url)
    except Exception as e:
        print(f"\n[ERRO] Falha ao conectar ao PostgreSQL: {e}\n")
        sys.exit(1)

    # Garantir que o schema e tabelas existam no PostgreSQL
    os.environ["DATABASE_URL"] = pg_url
    from app.services.database import init_db
    init_db()
    print("[+] Schema inicializado/validado no PostgreSQL.")

    print("\nIniciando transferência dos DADOS BASE operacionais:")

    # 1. Configurações Institucionais (Brasão, Prefeitura, Secretaria)
    migrate_table(
        s_conn, p_conn,
        table_name="system_settings",
        pkey="key",
        columns=["key", "value"]
    )

    # 2. Usuários e Perfis de Acesso (Administrador, Coordenador, Professores)
    migrate_table(
        s_conn, p_conn,
        table_name="users",
        pkey="id",
        columns=["id", "username", "name", "email", "role", "password_hash", "is_active", "created_at", "last_login"]
    )

    # 3. Escolas, Turmas e Alunos (Opcional ou quando --with-schools / --all for passado)
    if args.with_schools or args.all:
        print("\nTransferindo Estrutura Escolar Cadastrada:")
        migrate_table(
            s_conn, p_conn,
            table_name="schools",
            pkey="id",
            columns=["id", "name", "inep_code", "created_at"]
        )
        migrate_table(
            s_conn, p_conn,
            table_name="classrooms",
            pkey="id",
            columns=["id", "school_id", "name", "grade_year", "shift", "created_at"]
        )
        migrate_table(
            s_conn, p_conn,
            table_name="students",
            pkey="id",
            columns=["id", "school_id", "classroom_id", "registration", "name", "created_at"]
        )
    else:
        print("\n[i] Estrutura escolar (escolas, turmas e alunos) mantida vazia para novo cadastro.")
        print("    (Para incluir o cadastro escolar, execute com a flag --with-schools)")

    # 4. Provas e Submissões (Apenas quando --all for explicitamente fornecido)
    if args.all:
        print("\nTransferindo Provas e Histórico de Correções (--all ativo):")
        migrate_table(
            s_conn, p_conn,
            table_name="exams",
            pkey="id",
            columns=[
                "id", "title", "institution", "num_questions", "num_alternatives",
                "points_per_question", "answer_key", "weights", "sheet_template",
                "subtitle", "school_name", "classroom", "student_name", "shift",
                "logo_path", "created_at"
            ]
        )
        migrate_table(
            s_conn, p_conn,
            table_name="classroom_exams",
            pkey="classroom_id, exam_id",
            columns=["classroom_id", "exam_id", "created_at"]
        )
        migrate_table(
            s_conn, p_conn,
            table_name="submissions",
            pkey="id",
            columns=[
                "id", "exam_id", "student_name", "student_id", "classroom_id",
                "school_id", "score", "max_score", "detected_answers",
                "results_detail", "scanned_image_url", "overlay_image_url", "created_at"
            ]
        )
    else:
        print("[i] Histórico de testes e gabaritos antigos NÃO migrado (banco limpo para produção).")

    s_conn.close()
    p_conn.close()

    print("\n" + "="*70)
    print("  MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("  O banco PostgreSQL está pronto para uso em produção.")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
