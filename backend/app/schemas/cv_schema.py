"""
Schemas Pydantic para CV.
No exponer información interna como rutas o nombres de archivo internos.
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_serializer


class CVResponse(BaseModel):
    """Respuesta con info del CV. No expone filename interno ni storage_path."""
    id: UUID
    original_filename: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('id')
    def serialize_id(self, id: UUID) -> str:
        return str(id)


class CVUploadResponse(BaseModel):
    message: str
    cv: CVResponse


class CVDeleteResponse(BaseModel):
    message: str
