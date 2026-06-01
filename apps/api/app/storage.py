import httpx

from app.config import get_settings


async def store_resume_file(user_id: str, file_name: str, content: bytes) -> str | None:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None

    safe_name = file_name.replace("/", "_").replace("\\", "_")
    object_path = f"{user_id}/{safe_name}"
    endpoint = (
        f"{str(settings.supabase_url).rstrip('/')}/storage/v1/object/"
        f"{settings.supabase_resume_bucket}/{object_path}"
    )
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
        "x-upsert": "true",
        "content-type": "application/octet-stream",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(endpoint, content=content, headers=headers, timeout=30)
        response.raise_for_status()
    return object_path
