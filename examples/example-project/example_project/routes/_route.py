from fastapi import APIRouter, Depends

from example_project.providers import DatabaseProvider
from .dependencies import get_database_provider

router = APIRouter()

@router.get("/health")
async def validate_health(database_provider: DatabaseProvider = Depends(get_database_provider)):
    return {"status":await database_provider.healthcheck()}

