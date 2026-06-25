from sqlalchemy import text

from backend.core.db import get_connection


def fetch_user_by_email(email: str):
    """Fetch one user row by email."""
    sql = text(
        """
        SELECT
            user_id,
            email,
            password_hash,
            role,
            is_active,
            created_at
        FROM app_user
        WHERE email = :email
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql, {"email": email}).mappings().first()

    return dict(row) if row is not None else None


def fetch_user_by_id(user_id: int):
    """Fetch one user row by ID."""
    sql = text(
        """
        SELECT
            user_id,
            email,
            password_hash,
            role,
            is_active,
            created_at
        FROM app_user
        WHERE user_id = :user_id
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql, {"user_id": user_id}).mappings().first()

    return dict(row) if row is not None else None


def insert_user(email: str, password_hash: str, role: str):
    """Insert one user and return the created row."""
    insert_sql = text(
        """
        INSERT INTO app_user (email, password_hash, role, is_active)
        VALUES (:email, :password_hash, :role, 1)
        """
    )

    with get_connection() as conn:
        result = conn.execute(
            insert_sql,
            {
                "email": email,
                "password_hash": password_hash,
                "role": role,
            },
        )
        conn.commit()
        created_id = int(result.lastrowid)

    return fetch_user_by_id(created_id)


def upsert_pending_registration(email: str, password_hash: str, role: str, token_hash: str, expires_at):
    """Create or replace one pending registration by email."""
    sql = text(
        """
        INSERT INTO app_pending_registration (
            email,
            password_hash,
            role,
            verification_token_hash,
            expires_at,
            consumed_at
        )
        VALUES (
            :email,
            :password_hash,
            :role,
            :verification_token_hash,
            :expires_at,
            NULL
        )
        ON DUPLICATE KEY UPDATE
            password_hash = VALUES(password_hash),
            role = VALUES(role),
            verification_token_hash = VALUES(verification_token_hash),
            expires_at = VALUES(expires_at),
            consumed_at = NULL
        """
    )

    with get_connection() as conn:
        conn.execute(
            sql,
            {
                "email": email,
                "password_hash": password_hash,
                "role": role,
                "verification_token_hash": token_hash,
                "expires_at": expires_at,
            },
        )
        conn.commit()


def fetch_active_pending_registration_by_token_hash(token_hash: str):
    """Fetch one non-consumed, non-expired pending registration by token hash."""
    sql = text(
        """
        SELECT
            pending_registration_id,
            email,
            password_hash,
            role,
            verification_token_hash,
            expires_at,
            consumed_at,
            created_at,
            updated_at
        FROM app_pending_registration
        WHERE verification_token_hash = :verification_token_hash
          AND consumed_at IS NULL
          AND expires_at > UTC_TIMESTAMP()
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql, {"verification_token_hash": token_hash}).mappings().first()

    return dict(row) if row is not None else None


def fetch_active_pending_registration_by_email(email: str):
    """Fetch one non-consumed, non-expired pending registration by email."""
    sql = text(
        """
        SELECT
            pending_registration_id,
            email,
            password_hash,
            role,
            verification_token_hash,
            expires_at,
            consumed_at,
            created_at,
            updated_at
        FROM app_pending_registration
        WHERE email = :email
          AND consumed_at IS NULL
          AND expires_at > UTC_TIMESTAMP()
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql, {"email": email}).mappings().first()

    return dict(row) if row is not None else None


def consume_pending_registration(pending_registration_id: int):
    """Mark one pending registration as consumed."""
    sql = text(
        """
        UPDATE app_pending_registration
        SET consumed_at = UTC_TIMESTAMP()
        WHERE pending_registration_id = :pending_registration_id
          AND consumed_at IS NULL
        """
    )

    with get_connection() as conn:
        conn.execute(sql, {"pending_registration_id": pending_registration_id})
        conn.commit()


def fetch_active_admin_user():
    """Fetch one active admin user if present."""
    sql = text(
        """
        SELECT
            user_id,
            email,
            password_hash,
            role,
            is_active,
            created_at
        FROM app_user
        WHERE role = 'admin'
          AND is_active = 1
        ORDER BY user_id
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql).mappings().first()

    return dict(row) if row is not None else None


def upsert_admin_user(email: str, password_hash: str):
    """Create or update one admin user by email and return the resulting row."""
    upsert_sql = text(
        """
        INSERT INTO app_user (email, password_hash, role, is_active)
        VALUES (:email, :password_hash, 'admin', 1)
        ON DUPLICATE KEY UPDATE
            password_hash = VALUES(password_hash),
            role = 'admin',
            is_active = 1
        """
    )

    with get_connection() as conn:
        conn.execute(upsert_sql, {"email": email, "password_hash": password_hash})
        conn.commit()

    return fetch_user_by_email(email)


def insert_refresh_token(user_id: int, token_hash: str, expires_at):
    """Persist one refresh token row and return its id."""
    sql = text(
        """
        INSERT INTO app_refresh_token (
            user_id,
            token_hash,
            expires_at,
            revoked_at,
            replaced_by_token_id
        )
        VALUES (
            :user_id,
            :token_hash,
            :expires_at,
            NULL,
            NULL
        )
        """
    )

    with get_connection() as conn:
        result = conn.execute(
            sql,
            {
                "user_id": user_id,
                "token_hash": token_hash,
                "expires_at": expires_at,
            },
        )
        conn.commit()
        return int(result.lastrowid)


def fetch_refresh_token_by_hash(token_hash: str):
    """Fetch refresh token row by hash regardless of active/revoked state."""
    sql = text(
        """
        SELECT
            refresh_token_id,
            user_id,
            token_hash,
            expires_at,
            revoked_at,
            replaced_by_token_id,
            created_at
        FROM app_refresh_token
        WHERE token_hash = :token_hash
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql, {"token_hash": token_hash}).mappings().first()

    return dict(row) if row is not None else None


def fetch_active_refresh_token_by_hash(token_hash: str):
    """Fetch active (non-revoked, non-expired) refresh token row by hash."""
    sql = text(
        """
        SELECT
            refresh_token_id,
            user_id,
            token_hash,
            expires_at,
            revoked_at,
            replaced_by_token_id,
            created_at
        FROM app_refresh_token
        WHERE token_hash = :token_hash
          AND revoked_at IS NULL
          AND expires_at > UTC_TIMESTAMP()
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql, {"token_hash": token_hash}).mappings().first()

    return dict(row) if row is not None else None


def revoke_refresh_token(refresh_token_id: int, replaced_by_token_id: int | None = None):
    """Revoke one refresh token row if it is still active."""
    sql = text(
        """
        UPDATE app_refresh_token
        SET
            revoked_at = UTC_TIMESTAMP(),
            replaced_by_token_id = :replaced_by_token_id
        WHERE refresh_token_id = :refresh_token_id
          AND revoked_at IS NULL
        """
    )

    with get_connection() as conn:
        conn.execute(
            sql,
            {
                "refresh_token_id": refresh_token_id,
                "replaced_by_token_id": replaced_by_token_id,
            },
        )
        conn.commit()


def revoke_user_refresh_tokens(user_id: int):
    """Revoke all active refresh tokens for a user."""
    sql = text(
        """
        UPDATE app_refresh_token
        SET revoked_at = UTC_TIMESTAMP()
        WHERE user_id = :user_id
          AND revoked_at IS NULL
        """
    )

    with get_connection() as conn:
        conn.execute(sql, {"user_id": user_id})
        conn.commit()
