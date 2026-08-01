"""Integration tests for doc §6.2: auction document uploads (registration/
inspection/service/other), visibility (public/private), and secure download."""
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Category, User

PDF_BYTES = b"%PDF-1.4\n%fake pdf content for tests\n"


async def _create_auction(async_client: AsyncClient, seller_headers: dict, test_category: Category) -> str:
    payload = {
        "title": "Doc Upload Test Auction",
        "description": "Auction used to test document uploads",
        "category_id": test_category.id,
        "start_price": 1000.0,
        "min_increment": 50.0,
        "end_time": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "declaration_accepted": True,
    }
    response = await async_client.post("/api/auctions", json=payload, headers=seller_headers)
    assert response.status_code == 201
    return response.json()["id"]


class TestUploadDocuments:
    async def test_seller_uploads_registration_document(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category
    ):
        auction_id = await _create_auction(async_client, seller_headers, test_category)
        response = await async_client.post(
            f"/api/uploads/documents?auction_id={auction_id}&doc_category=registration",
            files=[("files", ("reg.pdf", PDF_BYTES, "application/pdf"))],
            headers=seller_headers,
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert len(data) == 1
        assert data[0]["media_type"] == "document"
        assert data[0]["doc_category"] == "registration"
        # doc §6.2: admin decides what's public - defaults to private
        assert data[0]["visibility"] == "private"
        # never a directly-guessable static URL - always the authorizing route
        assert data[0]["image_url"] == f"/api/uploads/{data[0]['id']}/download"

    async def test_rejects_invalid_doc_category(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category
    ):
        auction_id = await _create_auction(async_client, seller_headers, test_category)
        response = await async_client.post(
            f"/api/uploads/documents?auction_id={auction_id}&doc_category=not_a_real_category",
            files=[("files", ("reg.pdf", PDF_BYTES, "application/pdf"))],
            headers=seller_headers,
        )
        assert response.status_code == 400

    async def test_rejects_invalid_file_type_without_saving_others(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category
    ):
        """Unlike the photo batch endpoint's silent skip, a bad document must
        reject the whole request (400) - not silently drop just that file."""
        auction_id = await _create_auction(async_client, seller_headers, test_category)
        response = await async_client.post(
            f"/api/uploads/documents?auction_id={auction_id}&doc_category=service",
            files=[
                ("files", ("good.pdf", PDF_BYTES, "application/pdf")),
                ("files", ("bad.exe", b"not a real doc", "application/x-msdownload")),
            ],
            headers=seller_headers,
        )
        assert response.status_code == 400

        # Confirm nothing was saved from the rejected batch
        list_response = await async_client.get(f"/api/auctions/{auction_id}", headers=seller_headers)
        assert list_response.json()["images"] == []

    async def test_non_owner_seller_cannot_upload(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category, auth_headers: dict
    ):
        auction_id = await _create_auction(async_client, seller_headers, test_category)
        response = await async_client.post(
            f"/api/uploads/documents?auction_id={auction_id}&doc_category=other",
            files=[("files", ("reg.pdf", PDF_BYTES, "application/pdf"))],
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestDocumentVisibility:
    async def test_private_document_hidden_from_anonymous_and_other_users(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category, auth_headers: dict
    ):
        auction_id = await _create_auction(async_client, seller_headers, test_category)
        await async_client.post(
            f"/api/uploads/documents?auction_id={auction_id}&doc_category=inspection",
            files=[("files", ("insp.pdf", PDF_BYTES, "application/pdf"))],
            headers=seller_headers,
        )

        anon = await async_client.get(f"/api/auctions/{auction_id}")
        assert anon.json()["images"] == []

        other_user = await async_client.get(f"/api/auctions/{auction_id}", headers=auth_headers)
        assert other_user.json()["images"] == []

        owner = await async_client.get(f"/api/auctions/{auction_id}", headers=seller_headers)
        assert len(owner.json()["images"]) == 1

    async def test_private_document_visible_to_admin(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category, admin_headers: dict
    ):
        auction_id = await _create_auction(async_client, seller_headers, test_category)
        await async_client.post(
            f"/api/uploads/documents?auction_id={auction_id}&doc_category=service",
            files=[("files", ("svc.pdf", PDF_BYTES, "application/pdf"))],
            headers=seller_headers,
        )
        response = await async_client.get(f"/api/auctions/{auction_id}", headers=admin_headers)
        assert len(response.json()["images"]) == 1

    async def test_admin_can_make_document_public(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category, admin_headers: dict, auth_headers: dict
    ):
        auction_id = await _create_auction(async_client, seller_headers, test_category)
        upload = await async_client.post(
            f"/api/uploads/documents?auction_id={auction_id}&doc_category=other",
            files=[("files", ("doc.pdf", PDF_BYTES, "application/pdf"))],
            headers=seller_headers,
        )
        image_id = upload.json()[0]["id"]

        toggle = await async_client.put(
            f"/api/admin/auction-images/{image_id}/visibility?visibility=public", headers=admin_headers,
        )
        assert toggle.status_code == 200
        assert toggle.json()["visibility"] == "public"

        other_user = await async_client.get(f"/api/auctions/{auction_id}", headers=auth_headers)
        assert len(other_user.json()["images"]) == 1

    async def test_non_admin_cannot_toggle_visibility(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category,
    ):
        auction_id = await _create_auction(async_client, seller_headers, test_category)
        upload = await async_client.post(
            f"/api/uploads/documents?auction_id={auction_id}&doc_category=other",
            files=[("files", ("doc.pdf", PDF_BYTES, "application/pdf"))],
            headers=seller_headers,
        )
        image_id = upload.json()[0]["id"]
        response = await async_client.put(
            f"/api/admin/auction-images/{image_id}/visibility?visibility=public", headers=seller_headers,
        )
        assert response.status_code == 403


class TestSecureDownload:
    async def test_owner_can_download_private_document(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category
    ):
        auction_id = await _create_auction(async_client, seller_headers, test_category)
        upload = await async_client.post(
            f"/api/uploads/documents?auction_id={auction_id}&doc_category=registration",
            files=[("files", ("reg.pdf", PDF_BYTES, "application/pdf"))],
            headers=seller_headers,
        )
        image_id = upload.json()[0]["id"]
        response = await async_client.get(f"/api/uploads/{image_id}/download", headers=seller_headers)
        assert response.status_code == 200
        assert response.content == PDF_BYTES

    async def test_anonymous_cannot_download_private_document(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category
    ):
        auction_id = await _create_auction(async_client, seller_headers, test_category)
        upload = await async_client.post(
            f"/api/uploads/documents?auction_id={auction_id}&doc_category=registration",
            files=[("files", ("reg.pdf", PDF_BYTES, "application/pdf"))],
            headers=seller_headers,
        )
        image_id = upload.json()[0]["id"]
        response = await async_client.get(f"/api/uploads/{image_id}/download")
        assert response.status_code == 401

    async def test_other_user_cannot_download_private_document(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category, auth_headers: dict
    ):
        auction_id = await _create_auction(async_client, seller_headers, test_category)
        upload = await async_client.post(
            f"/api/uploads/documents?auction_id={auction_id}&doc_category=registration",
            files=[("files", ("reg.pdf", PDF_BYTES, "application/pdf"))],
            headers=seller_headers,
        )
        image_id = upload.json()[0]["id"]
        response = await async_client.get(f"/api/uploads/{image_id}/download", headers=auth_headers)
        assert response.status_code == 403

    async def test_anonymous_can_download_public_document(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category, admin_headers: dict
    ):
        auction_id = await _create_auction(async_client, seller_headers, test_category)
        upload = await async_client.post(
            f"/api/uploads/documents?auction_id={auction_id}&doc_category=other",
            files=[("files", ("doc.pdf", PDF_BYTES, "application/pdf"))],
            headers=seller_headers,
        )
        image_id = upload.json()[0]["id"]
        await async_client.put(f"/api/admin/auction-images/{image_id}/visibility?visibility=public", headers=admin_headers)

        response = await async_client.get(f"/api/uploads/{image_id}/download")
        assert response.status_code == 200
        assert response.content == PDF_BYTES
