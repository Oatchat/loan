import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from ..config import settings
from ..db import get_session
from ..deps import get_current_user
from ..models import Attachment, Debtor, User
from ..schemas import AttachmentOut


router = APIRouter(prefix="/debtors/{debtor_id}/attachments", tags=["attachments"])

ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/webp",
    "application/pdf",
}
MAX_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CATEGORIES = {"contract", "id_card", "slip", "collateral"}


@router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    debtor_id: int,
    category: str = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=400, detail="หมวดเอกสารไม่ถูกต้อง")
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="ประเภทไฟล์ไม่รองรับ (jpg/png/webp/pdf เท่านั้น)")
    d = session.get(Debtor, debtor_id)
    if not d:
        raise HTTPException(status_code=404, detail="ไม่พบลูกหนี้")

    body = await file.read()
    if len(body) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="ไฟล์ใหญ่เกิน 10MB")

    upload_root = Path(settings.upload_dir) / str(debtor_id)
    upload_root.mkdir(parents=True, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1] or ""
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = upload_root / stored_name
    stored_path.write_bytes(body)

    a = Attachment(
        debtor_id=debtor_id,
        category=category,
        filename=stored_name,
        original_name=file.filename or stored_name,
        size=len(body),
        mime_type=file.content_type or "application/octet-stream",
    )
    session.add(a)
    session.commit()
    session.refresh(a)
    return a


@router.get("/{attachment_id}/download")
def download_attachment(
    debtor_id: int,
    attachment_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    a = session.get(Attachment, attachment_id)
    if not a or a.debtor_id != debtor_id:
        raise HTTPException(status_code=404, detail="ไม่พบไฟล์")
    path = Path(settings.upload_dir) / str(debtor_id) / a.filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="ไฟล์หายไป")
    return FileResponse(path, media_type=a.mime_type, filename=a.original_name)


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    debtor_id: int,
    attachment_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    a = session.get(Attachment, attachment_id)
    if not a or a.debtor_id != debtor_id:
        raise HTTPException(status_code=404, detail="ไม่พบไฟล์")
    path = Path(settings.upload_dir) / str(debtor_id) / a.filename
    if path.exists():
        path.unlink()
    session.delete(a)
    session.commit()
    return None
