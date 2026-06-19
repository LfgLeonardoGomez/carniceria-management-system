import shutil
from pathlib import Path
from typing import Union

import magic
from fastapi import UploadFile

MAX_LOGO_SIZE = 2 * 1024 * 1024  # 2 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}


async def save_logo(empresa_id: Union[str, "uuid.UUID"], file: UploadFile, upload_path: Path) -> str:
    """Guarda el logo de una empresa en el filesystem.

    Args:
        empresa_id: UUID de la empresa.
        file: Archivo subido vía FastAPI UploadFile.
        upload_path: Directorio base donde se almacenan los uploads.

    Returns:
        Path relativo del logo guardado (ej: /uploads/empresas/{id}/logo.jpg).

    Raises:
        ValueError: Si el archivo excede el tamaño máximo, el MIME type no está permitido
                    o el formato es SVG.
    """
    # Leer en chunks para no bloquear el event loop
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(8192)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_LOGO_SIZE:
            raise ValueError(f"El archivo excede el tamaño máximo permitido de {MAX_LOGO_SIZE} bytes")
        chunks.append(chunk)

    data = b"".join(chunks)

    # Validar MIME type real con libmagic
    mime_type = magic.from_buffer(data, mime=True)
    if mime_type in {"image/svg+xml", "image/svg"}:
        raise ValueError("SVG no permitido")
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Tipo de imagen no permitido: {mime_type}")

    # Extensión segura basada en filename
    original_name = file.filename or "logo.bin"
    suffix = Path(original_name).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png"}:
        raise ValueError(f"Extensión de archivo no permitida: {suffix}")

    ext = "jpg" if suffix in {".jpg", ".jpeg"} else "png"

    # Limpiar logo anterior si existe
    await delete_existing_logo(str(empresa_id), upload_path)

    # Guardar archivo
    target_dir = upload_path / "empresas" / str(empresa_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"logo.{ext}"

    loop = __import__("asyncio").get_event_loop()
    await loop.run_in_executor(None, target_path.write_bytes, data)

    return f"/uploads/empresas/{empresa_id}/logo.{ext}"


async def delete_existing_logo(empresa_id: Union[str, "uuid.UUID"], upload_path: Path) -> None:
    """Elimina cualquier logo previo de la empresa (jpg o png)."""
    target_dir = upload_path / "empresas" / str(empresa_id)
    if not target_dir.exists():
        return

    for ext in ("jpg", "png"):
        logo_file = target_dir / f"logo.{ext}"
        if logo_file.exists():
            loop = __import__("asyncio").get_event_loop()
            await loop.run_in_executor(None, logo_file.unlink)
