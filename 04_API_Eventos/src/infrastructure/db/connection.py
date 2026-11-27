"""Conexión psycopg (v3) con prepare_threshold=None para Supavisor (pooler 6543)."""
import psycopg
from psycopg.rows import dict_row


def get_connection(database_url: str):
    return psycopg.connect(database_url, prepare_threshold=None, row_factory=dict_row, connect_timeout=15)
