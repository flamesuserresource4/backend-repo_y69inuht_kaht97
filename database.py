import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

# Initialize MongoDB client using environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "app_db")

_client: Optional[MongoClient] = None
_db: Optional[Database] = None

try:
    _client = MongoClient(DATABASE_URL, serverSelectionTimeoutMS=5000)
    # Trigger a server selection to validate connection
    _client.server_info()
    _db = _client[DATABASE_NAME]
except Exception:
    _client = None
    _db = None


def _get_collection(name: str) -> Collection:
    if _db is None:
        raise RuntimeError("Database not initialized. Check DATABASE_URL/NAME envs.")
    return _db[name]

# Public handle for other modules
db = _db


def create_document(collection_name: str, data: Dict[str, Any]) -> str:
    col = _get_collection(collection_name)
    now = datetime.utcnow()
    data.setdefault("created_at", now)
    data.setdefault("updated_at", now)
    result = col.insert_one(data)
    return str(result.inserted_id)


def get_documents(collection_name: str, filter_dict: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
    col = _get_collection(collection_name)
    docs = list(col.find(filter_dict or {}).limit(limit))
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


def get_document_by_id(collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    from bson import ObjectId
    col = _get_collection(collection_name)
    try:
        obj = col.find_one({"_id": ObjectId(doc_id)})
        if not obj:
            return None
        obj["id"] = str(obj.pop("_id"))
        return obj
    except Exception:
        return None


def update_document(collection_name: str, doc_id: str, data: Dict[str, Any]) -> bool:
    from bson import ObjectId
    col = _get_collection(collection_name)
    data["updated_at"] = datetime.utcnow()
    result = col.update_one({"_id": ObjectId(doc_id)}, {"$set": data})
    return result.modified_count > 0


def delete_document(collection_name: str, doc_id: str) -> bool:
    from bson import ObjectId
    col = _get_collection(collection_name)
    result = col.delete_one({"_id": ObjectId(doc_id)})
    return result.deleted_count > 0
