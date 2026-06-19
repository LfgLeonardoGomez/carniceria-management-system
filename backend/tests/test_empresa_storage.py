import io
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import UploadFile

from src.modules.empresa.storage import save_logo, delete_existing_logo, MAX_LOGO_SIZE, ALLOWED_MIME_TYPES


class TestSaveLogo:
    @pytest.fixture
    def upload_path(self, tmp_path: Path) -> Path:
        return tmp_path / "uploads"

    @pytest.fixture
    def empresa_id(self) -> str:
        return "123e4567-e89b-12d3-a456-426614174000"

    async def test_guarda_jpg_valido(self, upload_path: Path, empresa_id: str):
        content = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"x" * 100
        file = UploadFile(filename="logo.jpg", file=io.BytesIO(content))

        result = await save_logo(empresa_id, file, upload_path)

        assert result == f"/uploads/empresas/{empresa_id}/logo.jpg"
        saved = upload_path / "empresas" / empresa_id / "logo.jpg"
        assert saved.exists()
        assert saved.read_bytes() == content

    async def test_guarda_png_valido(self, upload_path: Path, empresa_id: str):
        # Minimal valid PNG header + IHDR chunk so libmagic recognizes it
        content = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        file = UploadFile(filename="logo.png", file=io.BytesIO(content))

        result = await save_logo(empresa_id, file, upload_path)

        assert result == f"/uploads/empresas/{empresa_id}/logo.png"

    async def test_rechaza_svg(self, upload_path: Path, empresa_id: str):
        content = b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"
        file = UploadFile(filename="logo.svg", file=io.BytesIO(content))

        with pytest.raises(ValueError, match="SVG no permitido"):
            await save_logo(empresa_id, file, upload_path)

    async def test_rechaza_mime_spoofing(self, upload_path: Path, empresa_id: str):
        # exe renombrado a jpg
        content = b"MZ\x90\x00" + b"x" * 100
        file = UploadFile(filename="logo.jpg", file=io.BytesIO(content))

        with pytest.raises(ValueError, match="Tipo de imagen no permitido"):
            await save_logo(empresa_id, file, upload_path)

    async def test_rechaza_tamano_excedido(self, upload_path: Path, empresa_id: str):
        content = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"x" * (MAX_LOGO_SIZE + 10)
        file = UploadFile(filename="logo.jpg", file=io.BytesIO(content))

        with pytest.raises(ValueError, match="excede el tamaño máximo"):
            await save_logo(empresa_id, file, upload_path)

    async def test_rechaza_bmp(self, upload_path: Path, empresa_id: str):
        content = b"BM" + b"\x00" * 100
        file = UploadFile(filename="logo.bmp", file=io.BytesIO(content))

        with pytest.raises(ValueError, match="Tipo de imagen no permitido"):
            await save_logo(empresa_id, file, upload_path)

    async def test_sobreescribe_logo_existente(self, upload_path: Path, empresa_id: str):
        content_old = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"old" * 10
        file_old = UploadFile(filename="logo.jpg", file=io.BytesIO(content_old))
        await save_logo(empresa_id, file_old, upload_path)

        content_new = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        file_new = UploadFile(filename="logo.png", file=io.BytesIO(content_new))
        result = await save_logo(empresa_id, file_new, upload_path)

        assert result == f"/uploads/empresas/{empresa_id}/logo.png"
        saved_dir = upload_path / "empresas" / empresa_id
        assert (saved_dir / "logo.png").exists()
        # old jpg should be gone
        assert not (saved_dir / "logo.jpg").exists()


class TestDeleteExistingLogo:
    async def test_elimina_logo_existente(self, tmp_path: Path):
        empresa_id = "123e4567-e89b-12d3-a456-426614174000"
        logo_dir = tmp_path / "empresas" / empresa_id
        logo_dir.mkdir(parents=True)
        (logo_dir / "logo.jpg").write_bytes(b"data")

        await delete_existing_logo(empresa_id, tmp_path)

        assert not (logo_dir / "logo.jpg").exists()

    async def test_no_falla_si_no_existe(self, tmp_path: Path):
        empresa_id = "123e4567-e89b-12d3-a456-426614174000"
        # no logo present
        await delete_existing_logo(empresa_id, tmp_path)
        assert True
