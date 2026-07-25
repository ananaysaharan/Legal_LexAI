from supabase import create_client, Client
from src.api.config import settings

def get_supabase_client() -> Client:
    """
    Creates and returns a Supabase client using the Service Role key.
    This allows the backend to bypass Row Level Security and manage files.
    """
    return create_client(settings.supabase_url, settings.supabase_key)

class StorageService:
    def __init__(self, bucket_name: str = "documents"):
        self.client = get_supabase_client()
        self.bucket = bucket_name

    async def upload_file(self, file_bytes: bytes, storage_path: str, content_type: str) -> str:
        """
        Uploads a file to Supabase Storage.
        """
        # Note: supabase-py storage methods are currently synchronous.
        # In a very high-throughput async app, we might wrap this in a threadpool
        # (run_in_executor) to prevent blocking the event loop.
        self.client.storage.from_(self.bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type}
        )
        return storage_path

    async def delete_file(self, storage_path: str) -> None:
        """
        Deletes a file from Supabase Storage.
        """
        self.client.storage.from_(self.bucket).remove([storage_path])

    async def download_file(self, storage_path: str) -> bytes:
        return self.client.storage.from_(self.bucket).download(storage_path)

storage_service = StorageService()
