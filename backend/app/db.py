from ZODB import FileStorage, DB
import transaction
import ZODB, ZODB.FileStorage
from BTrees.OOBTree import OOBTree
from persistent import Persistent

import os

DB_PATH = os.environ.get("ZODB_PATH", "routes.fs")

class Route(Persistent):
    def __init__(self, route_id, start_text, start_coords, end_text, end_coords, distance, duration, geometry, created_at):
        self.id = route_id
        self.start_text = start_text
        self.start_coords = start_coords  # [lon, lat]
        self.end_text = end_text
        self.end_coords = end_coords      # [lon, lat]
        self.distance = distance          # meters
        self.duration = duration          # seconds
        self.geometry = geometry          # GeoJSON LineString or encoded polyline
        self.created_at = created_at

def get_connection():
    storage = ZODB.FileStorage.FileStorage(DB_PATH)
    db = DB(storage)
    connection = db.open()
    return db, connection

def ensure_root(connection):
    root = connection.root()
    if "routes" not in root:
        root["routes"] = OOBTree()
        transaction.commit()
    return root

def close(db, connection):
    try:
        connection.close()
    finally:
        db.close()
