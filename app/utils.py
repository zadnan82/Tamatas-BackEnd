import uuid
import os
import boto3
from PIL import Image
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.config import settings


def generate_id():
    return str(uuid.uuid4())


def create_s3_client():
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        return boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
    return None


async def upload_file_to_s3(file: UploadFile, folder: str = "uploads") -> str:
    s3_client = create_s3_client()
    if not s3_client:
        # Fallback to local storage
        return await save_file_locally(file, folder)

    try:
        file_extension = file.filename.split(".")[-1]
        file_name = f"{folder}/{generate_id()}.{file_extension}"

        s3_client.upload_fileobj(
            file.file,
            settings.aws_bucket_name,
            file_name,
            ExtraArgs={"ContentType": file.content_type},
        )

        return f"https://{settings.aws_bucket_name}.s3.{settings.aws_region}.amazonaws.com/{file_name}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


async def save_file_locally(file: UploadFile, folder: str = "uploads") -> str:
    try:
        os.makedirs(f"uploads/{folder}", exist_ok=True)
        file_extension = file.filename.split(".")[-1]
        file_name = f"{generate_id()}.{file_extension}"
        file_path = f"uploads/{folder}/{file_name}"

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return f"/uploads/{folder}/{file_name}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save failed: {str(e)}")


def validate_image(file: UploadFile):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Check file size (5MB limit)
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")


def resize_image(image_path: str, max_size: tuple = (800, 600)):
    try:
        with Image.open(image_path) as img:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(image_path, optimize=True, quality=85)
    except Exception as e:
        print(f"Error resizing image: {e}")
