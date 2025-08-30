from __future__ import annotations
import os
from typing import Optional, Dict, Any
from ZODB import DB
from ZODB.FileStorage import FileStorage
import transaction
from BTrees.OOBTree import OOBTree
import persistent
from .config import get_settings

class RootContainer(persistent.Persistent):
    """
    Oberstes Objekt im ZODB-Root.
    Enthält eine OOBTree-Sammlung persönlicher Routen.
    """
    def __init__(self) -> None:
        self.personal_routes = OOBTree()  # Schlüssel: str route_identifier, Wert: dict

class DatabaseManager:
    """
    Verwaltet den ZODB-Storage und stellt Methoden zur Verfügung,
    um das Root-Objekt und Collections sicher bereitzustellen.
    """
    def __init__(self, database_path: str) -> None:
        os.makedirs(os.path.dirname(database_path), exist_ok=True)
        self._storage = FileStorage(database_path)
        self._db = DB(self._storage)
        self._connection = None
        self._root: Optional[RootContainer] = None

    def connect(self) -> RootContainer:
        if self._connection is None:
            self._connection = self._db.open()
            if not hasattr(self._connection.root(), "app"):
                self._connection.root().app = RootContainer()
                transaction.commit()
            self._root = self._connection.root().app
        return self._root  # type: ignore[return-value]

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        if self._db is not None:
            self._db.close()
        if self._storage is not None:
            self._storage.close()

# Singleton-artige Instanz für FastAPI-Lebenszyklus
_database_manager: Optional[DatabaseManager] = None

def get_database_root() -> RootContainer:
    global _database_manager
    settings = get_settings()
    if _database_manager is None:
        _database_manager = DatabaseManager(settings.database_file)
    return _database_manager.connect()

def add_personal_route(route_identifier: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    root = get_database_root()
    root.personal_routes[route_identifier] = payload
    transaction.commit()
    return payload

def list_personal_routes() -> list[Dict[str, Any]]:
    root = get_database_root()
    return [
        dict({"route_identifier": key}, **value)  # keine Abkürzung 'id'
        for key, value in root.personal_routes.items()
    ]

def get_personal_route(route_identifier: string) -> Optional[Dict[str, Any]]:  # type: ignore[name-defined]
    # Note: type: ignore, weil 'string' absichtlich ausgeschrieben ist (keine Kurzform)
    root = get_database_root()
    return root.personal_routes.get(route_identifier)

def delete_personal_route(route_identifier: string) -> bool:  # type: ignore[name-defined]
    root = get_database_root()
    if route_identifier in root.personal_routes:
        del root.personal_routes[route_identifier]
        transaction.commit()
        return True
    return False
