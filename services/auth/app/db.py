"""Data access for the auth schema (role auth_svc, search_path = auth)."""

from datetime import UTC, datetime

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from market_common.config import get_settings

_pool: ConnectionPool | None = None


def pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(get_settings().database_url, min_size=1, max_size=5, kwargs={"row_factory": dict_row})
    return _pool


def close() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


_USER_SQL = """
SELECT u.id, u.email, u.password_hash, u.is_active,
       coalesce(array_agg(r.name) FILTER (WHERE r.name IS NOT NULL), '{}') AS roles
FROM users u
LEFT JOIN user_roles ur ON ur.user_id = u.id
LEFT JOIN roles r ON r.id = ur.role_id
"""


def get_user_by_email(email: str) -> dict | None:
    with pool().connection() as conn:
        return conn.execute(_USER_SQL + " WHERE u.email = %s GROUP BY u.id", (email,)).fetchone()


def list_users() -> list[dict]:
    with pool().connection() as conn:
        rows = conn.execute(_USER_SQL + " GROUP BY u.id ORDER BY u.id").fetchall()
    return [{"id": r["id"], "email": r["email"], "roles": r["roles"]} for r in rows]


def create_user(email: str, password_hash: str, roles: list[str]) -> dict:
    with pool().connection() as conn, conn.transaction():
        user_id = conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id", (email, password_hash)
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO user_roles (user_id, role_id) SELECT %s, id FROM roles WHERE name = ANY(%s)",
            (user_id, roles),
        )
    return {"id": user_id, "email": email, "roles": roles}


def store_refresh_token(user_id: int, token_hash: str, expires_at: datetime) -> None:
    with pool().connection() as conn:
        conn.execute(
            "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
            (user_id, token_hash, expires_at),
        )


def consume_refresh_token(token_hash: str) -> dict | None:
    with pool().connection() as conn, conn.transaction():
        row = conn.execute(
            """UPDATE refresh_tokens SET revoked = true
               WHERE token_hash = %s AND NOT revoked AND expires_at > %s
               RETURNING user_id""",
            (token_hash, datetime.now(UTC)),
        ).fetchone()
        if not row:
            return None
        return conn.execute(_USER_SQL + " WHERE u.id = %s GROUP BY u.id", (row["user_id"],)).fetchone()


def get_service_account(name: str) -> dict | None:
    with pool().connection() as conn:
        return conn.execute(
            """SELECT sa.name, sa.api_key_hash, r.name AS role
               FROM service_accounts sa JOIN roles r ON r.id = sa.role_id WHERE sa.name = %s""",
            (name,),
        ).fetchone()


def upsert_service_account(name: str, api_key_hash: str) -> None:
    with pool().connection() as conn:
        conn.execute(
            """INSERT INTO service_accounts (name, api_key_hash, role_id)
               SELECT %s, %s, id FROM roles WHERE name = 'service_account'
               ON CONFLICT (name) DO UPDATE SET api_key_hash = EXCLUDED.api_key_hash""",
            (name, api_key_hash),
        )
