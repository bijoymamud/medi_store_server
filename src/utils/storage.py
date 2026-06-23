import os
import shutil
import uuid
from fastapi import UploadFile


def upload_file(file: UploadFile, folder: str = "uploads") -> str:
    """
    Uploads a file to a configured storage backend.
    Checks cloud providers in order of preference:
      1. Cloudinary
      2. AWS S3
      3. Fallback: Local file system

    Returns:
      The absolute URL (for cloud storage) or relative path (for local storage).
      Returns "" on failure.
    """
    if not file or not file.filename:
        print("upload_file: No file or filename provided.")
        return ""

    # 1. Cloudinary Integration
    cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY")
    cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET")

    if cloudinary_cloud_name and cloudinary_api_key and cloudinary_api_secret:
        try:
            import cloudinary
            import cloudinary.uploader
            cloudinary.config(
                cloud_name=cloudinary_cloud_name,
                api_key=cloudinary_api_key,
                api_secret=cloudinary_api_secret,
                secure=True
            )
            # Seek to beginning before reading
            file.file.seek(0)
            response = cloudinary.uploader.upload(file.file, folder=folder)
            url = response.get("secure_url") or ""
            if url:
                return url
        except Exception as e:
            print(f"Cloudinary upload failed: {e}. Falling back to next provider...")
            # IMPORTANT: Seek back to the beginning so the next attempt can read the file
            try:
                file.file.seek(0)
            except Exception:
                pass

    # 2. AWS S3 Integration
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
    aws_region = os.getenv("AWS_REGION", "us-east-1")

    if aws_access_key and aws_secret_key and aws_bucket:
        try:
            import boto3
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            s3_key = f"{folder}/{unique_filename}"
            # Seek to beginning before reading
            file.file.seek(0)
            s3_client.upload_fileobj(file.file, aws_bucket, s3_key, ExtraArgs={"ACL": "public-read"})
            return f"https://{aws_bucket}.s3.{aws_region}.amazonaws.com/{s3_key}"
        except Exception as e:
            print(f"AWS S3 upload failed: {e}. Falling back to local storage...")
            # IMPORTANT: Seek back to the beginning so local fallback can read the file
            try:
                file.file.seek(0)
            except Exception:
                pass

    # 3. Fallback: Local file system
    try:
        file_ext = os.path.splitext(file.filename)[1]
        if not file_ext:
            file_ext = ".jpg"  # default extension if none provided
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        upload_dir = f"uploads/{folder}"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_filename)

        # Seek to beginning before reading
        try:
            file.file.seek(0)
        except Exception:
            pass

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Verify the file was actually written
        if os.path.getsize(file_path) == 0:
            os.remove(file_path)
            print(f"upload_file: Written file is empty, upload failed for {file.filename}")
            return ""

        saved_path = f"/uploads/{folder}/{unique_filename}"
        print(f"upload_file: Successfully saved to {saved_path}")
        return saved_path

    except Exception as e:
        print(f"Local file upload failed: {e}")
        return ""