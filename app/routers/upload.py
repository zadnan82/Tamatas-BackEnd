from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.auth import get_current_active_user
from app.models import User
from app.utils import validate_image, upload_file_to_s3, resize_image
from app.schemas import FileUpload

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/image", response_model=FileUpload)
async def upload_image(
    file: UploadFile = File(...), current_user: User = Depends(get_current_active_user)
):
    # Validate image
    validate_image(file)

    # Upload file
    file_url = await upload_file_to_s3(file, "images")

    return FileUpload(file_url=file_url, filename=file.filename)


@router.post("/images", response_model=List[FileUpload])
async def upload_multiple_images(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user),
):
    if len(files) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 files allowed")

    uploaded_files = []
    for file in files:
        validate_image(file)
        file_url = await upload_file_to_s3(file, "images")
        uploaded_files.append(FileUpload(file_url=file_url, filename=file.filename))

    return uploaded_files
