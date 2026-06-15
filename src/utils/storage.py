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
    """
    if not file or not file.filename:
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
            # Upload using the open file pointer
            response = cloudinary.uploader.upload(file.file, folder=folder)
            return response.get("secure_url") or ""
        except Exception as e:
            print(f"Cloudinary upload failed: {e}. Falling back...")

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
            unique_filename = f"{folder}/{uuid.uuid4()}{file_ext}"
            
            # Reset cursor and upload
            file.file.seek(0)
            s3_client.upload_fileobj(
                file.file,
                aws_bucket,
                unique_filename,
                ExtraArgs={'ContentType': file.content_type or 'image/jpeg'}
            )
            
            return f"https://{aws_bucket}.s3.{aws_region}.amazonaws.com/{unique_filename}"
        except Exception as e:
            print(f"AWS S3 upload failed: {e}. Falling back...")

    # 3. Fallback: Local File Storage
    try:
        local_dir = os.path.join("uploads", folder)
        os.makedirs(local_dir, exist_ok=True)
        
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{file_ext}"
        
        relative_url = f"/uploads/{folder}/{filename}"
        absolute_path = os.path.join(local_dir, filename)
        
        # Reset cursor and save to disk
        file.file.seek(0)
        with open(absolute_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return relative_url
    except Exception as e:
        print(f"Local file storage upload failed: {e}")
        return ""
