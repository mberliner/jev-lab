"""Estado local en SQLite: auditoría y cola de revisión (research.md R5; data-model.md).

Un archivo, `estado.sqlite3`, fuera del repositorio (FR-016). Solo traduce filas a entidades del
dominio con consultas parametrizadas; las reglas de transición son del dominio. Cada `record` y
cada `save_resolution` es una transacción.
"""

import json
import os
import sqlite3
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from jevlab.domain.diagnostics import StateUnreadable
from jevlab.domain.policy import ActionName, PolicyRef, Risk
from jevlab.domain.review import Resolution, ReviewAction, ReviewItem
from jevlab.domain.routing import ActionStatus, AuditEntry, PendingReason, RoutingResult
from jevlab.domain.triage import Origin

STATE_FILE = "estado.sqlite3"
_ENV = "JEVLAB_STATE_DIR"
_USER_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY, request_id TEXT NOT NULL, at TEXT NOT NULL, kind TEXT NOT NULL,
    action TEXT NOT NULL, value TEXT, confidence REAL, threshold REAL, risk TEXT NOT NULL,
    outcome TEXT NOT NULL, reasons TEXT NOT NULL, policy_version TEXT NOT NULL,
    policy_fingerprint TEXT NOT NULL, origin_mode TEXT NOT NULL, model TEXT NOT NULL,
    spec_versions TEXT NOT NULL, review_item INTEGER
);
CREATE TABLE IF NOT EXISTS review_item (
    id INTEGER PRIMARY KEY, request_id TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL,
    ticket TEXT NOT NULL, origin TEXT NOT NULL, policy_version TEXT NOT NULL,
    policy_fingerprint TEXT NOT NULL, spec_versions TEXT NOT NULL, queue TEXT
);
CREATE TABLE IF NOT EXISTS review_action (
    item_id INTEGER NOT NULL REFERENCES review_item(id), action TEXT NOT NULL, value TEXT,
    confidence REAL, threshold REAL NOT NULL, risk TEXT NOT NULL, justification TEXT NOT NULL,
    status TEXT NOT NULL, reasons TEXT NOT NULL, resolution TEXT,
    PRIMARY KEY (item_id, action)
);
"""


def state_dir(
    env: Mapping[str, str] | None = None, platform: str | None = None, home: Path | None = None
) -> Path:
    """`JEVLAB_STATE_DIR` si existe; si no, el directorio de estado del usuario. Lo crea.

    Por defecto, el entorno, la plataforma y la carpeta personal del proceso.
    """
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    configured = env.get(_ENV)
    if configured:
        folder = Path(configured)
    elif platform == "win32":
        base = env.get("LOCALAPPDATA")
        folder = (Path(base) if base else (home or Path.home()) / "AppData" / "Local") / "jevlab"
    else:
        base = env.get("XDG_STATE_HOME")
        folder = (Path(base) if base else (home or Path.home()) / ".local" / "state") / "jevlab"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def state_file() -> Path:
    return state_dir() / STATE_FILE


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class SqliteRoutingStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Abre, comprueba la versión del esquema y confirma o deshace al salir."""
        connection = sqlite3.connect(self.path)
        try:
            try:
                (version,) = connection.execute("PRAGMA user_version").fetchone()
                if version == 0:
                    connection.executescript(_SCHEMA)
                    connection.execute(f"PRAGMA user_version = {_USER_VERSION}")
                elif version != _USER_VERSION:
                    raise StateUnreadable(str(self.path))
            except sqlite3.DatabaseError:
                raise StateUnreadable(str(self.path)) from None
            with connection:
                yield connection
        finally:
            connection.close()

    def record(
        self, result: RoutingResult, entries: Sequence[AuditEntry], item: ReviewItem | None
    ) -> ReviewItem | None:
        with self._connect() as connection:
            saved = None
            if item is not None:
                saved = self._insert_item(connection, item)
            for entry in entries:
                if saved is not None:
                    entry = entry.model_copy(update={"review_item": saved.id})
                self._insert_audit(connection, entry)
            return saved

    def pending(self) -> list[ReviewItem]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT DISTINCT item_id FROM review_action WHERE resolution IS NULL "
                "ORDER BY item_id"
            ).fetchall()
            return [self._load_item(connection, item_id) for (item_id,) in rows]

    def get(self, item_id: int) -> ReviewItem | None:
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM review_item WHERE id = ?", (item_id,)
            ).fetchone()
            return None if exists is None else self._load_item(connection, item_id)

    def save_resolution(self, item: ReviewItem, entries: Sequence[AuditEntry]) -> None:
        if item.id is None:
            raise ValueError("solo se resuelve un elemento ya guardado")
        with self._connect() as connection:
            connection.execute(
                "UPDATE review_item SET queue = ? WHERE id = ?", (item.queue, item.id)
            )
            for action in item.actions:
                connection.execute(
                    "UPDATE review_action SET resolution = ? WHERE item_id = ? AND action = ?",
                    (
                        None if action.resolution is None else action.resolution.value,
                        item.id,
                        action.action.value,
                    ),
                )
            for entry in entries:
                self._insert_audit(connection, entry)

    def _insert_item(self, connection: sqlite3.Connection, item: ReviewItem) -> ReviewItem:
        cursor = connection.execute(
            "INSERT INTO review_item (request_id, created_at, ticket, origin, policy_version, "
            "policy_fingerprint, spec_versions, queue) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item.request_id,
                item.created_at.isoformat(),
                item.ticket,
                item.origin.model_dump_json(),
                item.policy.version,
                item.policy.fingerprint,
                _json(item.spec_versions),
                item.queue,
            ),
        )
        item_id = cursor.lastrowid
        assert item_id is not None
        for action in item.actions:
            connection.execute(
                "INSERT INTO review_action (item_id, action, value, confidence, threshold, risk, "
                "justification, status, reasons, resolution) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item_id,
                    action.action.value,
                    action.value,
                    action.confidence,
                    action.threshold,
                    action.risk.value,
                    action.justification,
                    action.status.value,
                    _json([r.value for r in action.reasons]),
                    None if action.resolution is None else action.resolution.value,
                ),
            )
        return item.model_copy(update={"id": item_id})

    def _insert_audit(self, connection: sqlite3.Connection, entry: AuditEntry) -> None:
        connection.execute(
            "INSERT INTO audit (request_id, at, kind, action, value, confidence, threshold, risk, "
            "outcome, reasons, policy_version, policy_fingerprint, origin_mode, model, "
            "spec_versions, review_item) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entry.request_id,
                entry.at.isoformat(),
                entry.kind,
                entry.action.value,
                entry.value,
                entry.confidence,
                entry.threshold,
                entry.risk.value,
                entry.outcome,
                _json([r.value for r in entry.reasons]),
                entry.policy.version,
                entry.policy.fingerprint,
                entry.origin_mode.value,
                entry.model,
                _json(entry.spec_versions),
                entry.review_item,
            ),
        )

    def _load_item(self, connection: sqlite3.Connection, item_id: int) -> ReviewItem:
        row = connection.execute(
            "SELECT request_id, created_at, ticket, origin, policy_version, policy_fingerprint, "
            "spec_versions, queue FROM review_item WHERE id = ?",
            (item_id,),
        ).fetchone()
        request_id, created_at, ticket, origin, version, fingerprint, versions, queue = row
        actions = connection.execute(
            "SELECT action, value, confidence, threshold, risk, justification, status, reasons, "
            "resolution FROM review_action WHERE item_id = ? ORDER BY rowid",
            (item_id,),
        ).fetchall()
        return ReviewItem(
            id=item_id,
            request_id=request_id,
            created_at=datetime.fromisoformat(created_at),
            ticket=ticket,
            origin=Origin.model_validate_json(origin),
            policy=PolicyRef(version=version, fingerprint=fingerprint),
            spec_versions=json.loads(versions),
            actions=tuple(
                ReviewAction(
                    action=ActionName(name),
                    value=value,
                    confidence=confidence,
                    threshold=threshold,
                    risk=Risk(risk),
                    justification=justification,
                    status=ActionStatus(status),
                    reasons=tuple(PendingReason(r) for r in json.loads(reasons)),
                    resolution=None if resolution is None else Resolution(resolution),
                )
                for (
                    name,
                    value,
                    confidence,
                    threshold,
                    risk,
                    justification,
                    status,
                    reasons,
                    resolution,
                ) in actions
            ),
            queue=queue,
        )
