"""Authenticated direct-upload admission; all object keys are server selected."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import get_active_tenant, get_current_user
from app.services.document_uploads import UploadError
from app.services.document_storage import StorageUnavailable

router = APIRouter(prefix='/jobs', tags=['documents'])


class UploadRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    filename: str = Field(min_length=1, max_length=240)
    file_size: int = Field(gt=0, le=20_000_000, strict=True)
    content_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    force_reprocess: bool = False


def get_upload_service(request: Request):
    service = getattr(request.app.state, 'document_uploads', None)
    if service is None:
        raise HTTPException(503, detail='document_uploads_unavailable')
    return service


def call(operation, *args):
    try:
        return operation(*args)
    except UploadError as error:
        raise HTTPException(error.status, detail=error.code) from None
    except StorageUnavailable:
        raise HTTPException(503, detail='document_storage_unavailable') from None


@router.post('/uploads', status_code=201)
def begin_upload(payload: UploadRequest, user=Depends(get_current_user), tenant=Depends(get_active_tenant),
                 service=Depends(get_upload_service)):
    return call(service.begin, tenant, user['id'], payload)


@router.post('/uploads/{upload_id}/confirm', status_code=202)
def confirm_upload(upload_id: str, user=Depends(get_current_user), tenant=Depends(get_active_tenant),
                   service=Depends(get_upload_service)):
    return call(service.confirm, upload_id, tenant, user['id'])


@router.get('/uploads/{upload_id}')
def upload_status(upload_id: str, user=Depends(get_current_user), tenant=Depends(get_active_tenant),
                  service=Depends(get_upload_service)):
    return call(service.status, upload_id, tenant, user['id'])


@router.delete('/uploads/{upload_id}')
def cancel_upload(upload_id: str, user=Depends(get_current_user), tenant=Depends(get_active_tenant),
                  service=Depends(get_upload_service)):
    return call(service.cancel, upload_id, tenant, user['id'])


@router.get('/documents/{job_id}')
def extracted_document(job_id: str, user=Depends(get_current_user), tenant=Depends(get_active_tenant),
                       service=Depends(get_upload_service)):
    return call(service.extracted, job_id, tenant)
