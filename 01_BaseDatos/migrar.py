"""
EventPass 360 — Migrador de Base de Datos (Fase 1 · SOA)
Ejecuta esquema.sql y datos.sql contra Supabase PostgreSQL (Transaction Pooler 6543).
Uso:  DATABASE_URL=postgresql://... python migrar.py
Nota: psycopg (v3) con prepare_threshold=None por Supavisor en modo transacción.
"""
import os
from pathlib import Path

import psycopg

BASE_DIR = Path(__file__).resolve().parent


def load_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip()
    raise SystemExit("DATABASE_URL no definida (usa .env local o variable de entorno).")


def split_statements(sql: str):
    statements = []
    for part in sql.split(";"):
        part = part.strip()
        if part:
            statements.append(part)
    return statements


def run_script(conn, path: Path):
    sql = path.read_text(encoding="utf-8")
    statements = split_statements(sql)
    for stmt in statements:
        conn.execute(stmt)
    print(f"[OK] {path.name}: {len(statements)} sentencias ejecutadas")


def verify(conn):
    tables = conn.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    ).fetchall()
    print("Tablas en public:", [t[0] for t in tables])
    for t in ["roles", "usuarios", "categorias", "eventos", "tipos_entrada",
              "promociones", "compras", "detalle_compra", "facturas"]:
        n = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} filas")


def main():
    url = load_database_url()
    print("Conectando a Supabase (pooler 6543)...")
    conn = psycopg.connect(url, prepare_threshold=None)
    conn.autocommit = True
    try:
        run_script(conn, BASE_DIR / "esquema.sql")
        run_script(conn, BASE_DIR / "datos.sql")
        print("--- Verificación ---")
        verify(conn)
    finally:
        conn.close()
    print("Migración completada.")


if __name__ == "__main__":
    main()
