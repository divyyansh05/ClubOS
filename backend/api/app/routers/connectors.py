from fastapi import APIRouter, HTTPException
from app.services.connector_service import (
    get_all_statuses,
    get_connector_data
)

router = APIRouter(prefix="/connectors", tags=["connectors"])

def status_to_dict(status):
    """Convert ConnectorStatus to dict"""
    return {
        "connector_id": status.connector_id,
        "name": status.name,
        "status": status.status,
        "last_sync": status.last_sync.isoformat() if status.last_sync else None,
        "records_fetched": status.records_fetched,
        "error_message": status.error_message,
        "auth_type": status.auth_type,
        "data_type": status.data_type,
    }

@router.get("/status")
def connector_status():
    statuses = get_all_statuses()
    return {
        "connectors": [status_to_dict(s) for s in statuses],
        "connected_count": sum(
            1 for s in statuses if s.status == "connected"
        ),
        "total_count": len(statuses)
    }

@router.get("/data/{connector_id}")
def connector_data(connector_id: str, days_back: int = 30):
    data = get_connector_data(connector_id, days_back)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Connector '{connector_id}' not found"
        )
    return data
