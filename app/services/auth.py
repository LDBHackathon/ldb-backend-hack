from typing import Any
from uuid import UUID, uuid4

from fastapi import status

from app.enums.merchant import MerchantStatus
from app.models.merchants import Merchant, MerchantApiKey
from app.schemas.requests.auth import (
    ChangePasswordRequestSchema,
    LoginAuthRequestSchema,
    RegisterAuthRequestSchema,
)
from app.schemas.requests.onboarding import (
    OnboardingAddressRequestSchema,
    OnboardingBusinessRequestSchema,
    OnboardingVerificationRequestSchema,
)
from app.utils.api_keys import api_key_prefix, generate_api_key, hash_api_key
from app.utils.exceptions import ErrorResponse
from app.utils.passwords import hash_password, verify_password
from app.utils.response_formatter import success_response


class AuthService:
    """Dashboard session registration and login."""

    async def register(self, body: RegisterAuthRequestSchema) -> dict[str, Any]:
        if await Merchant.filter(email=body.email).exists():
            raise ErrorResponse(
                status.HTTP_409_CONFLICT,
                "A merchant with this email already exists",
            )

        merchant = await Merchant.create(
            id=uuid4(),
            name=body.full_name,
            email=body.email,
            password_hash=hash_password(body.password),
            status=MerchantStatus.PENDING_KYB,
            kyb_data={"account": {"full_name": body.full_name, "email": body.email}},
        )
        raw_key = generate_api_key()
        await MerchantApiKey.create(
            id=uuid4(),
            merchant=merchant,
            key_hash=hash_api_key(raw_key),
            key_prefix=api_key_prefix(raw_key),
            name="default",
        )

        return success_response(
            status.HTTP_201_CREATED,
            "Merchant registered",
            data={
                "merchant": await self._merchant_payload(merchant),
                "api_key": raw_key,
            },
        )

    async def login(self, body: LoginAuthRequestSchema) -> dict[str, Any]:
        merchant = await Merchant.get_or_none(email=body.email)
        if not merchant or not verify_password(body.password, merchant.password_hash):
            raise ErrorResponse(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
        if merchant.status == MerchantStatus.SUSPENDED:
            raise ErrorResponse(status.HTTP_401_UNAUTHORIZED, "Merchant account suspended")

        return success_response(
            status.HTTP_200_OK,
            "Login successful",
            data={"merchant": await self._merchant_payload(merchant)},
        )

    async def me(self, merchant_id: UUID) -> dict[str, Any]:
        merchant = await Merchant.get_or_none(id=merchant_id)
        if not merchant:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND, "Merchant not found")
        return success_response(
            status.HTTP_200_OK,
            "Session active",
            data={"merchant": await self._merchant_payload(merchant)},
        )

    async def _merchant_payload(self, merchant: Merchant) -> dict[str, Any]:
        return {
            "id": merchant.id,
            "name": merchant.name,
            "email": merchant.email,
            "phone": merchant.phone,
            "status": merchant.status,
            "kyb_submitted": bool(merchant.kyb_data.get("submitted_at")),
            "created_at": merchant.created_at,
            "updated_at": merchant.updated_at,
        }


class OnboardingService:
    """KYB onboarding steps stored on merchant.kyb_data."""

    async def update_business(
        self, merchant_id: UUID, body: OnboardingBusinessRequestSchema
    ) -> dict[str, Any]:
        merchant = await self._get_merchant(merchant_id)
        merchant.kyb_data["business"] = body.model_dump(exclude_none=True)
        await merchant.save()
        return success_response(
            status.HTTP_200_OK,
            "Business details saved",
            data={"kyb_data": merchant.kyb_data},
        )

    async def update_address(
        self, merchant_id: UUID, body: OnboardingAddressRequestSchema
    ) -> dict[str, Any]:
        merchant = await self._get_merchant(merchant_id)
        merchant.kyb_data["address"] = body.model_dump(exclude_none=True)
        await merchant.save()
        return success_response(
            status.HTTP_200_OK,
            "Address details saved",
            data={"kyb_data": merchant.kyb_data},
        )

    async def update_verification(
        self, merchant_id: UUID, body: OnboardingVerificationRequestSchema
    ) -> dict[str, Any]:
        if not body.consent:
            raise ErrorResponse(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "Consent is required to continue",
            )
        merchant = await self._get_merchant(merchant_id)
        merchant.kyb_data["verification"] = body.model_dump(exclude_none=True)
        await merchant.save()
        return success_response(
            status.HTTP_200_OK,
            "Verification details saved",
            data={"kyb_data": merchant.kyb_data},
        )

    async def save_document(
        self,
        merchant_id: UUID,
        document_type: str,
        upload_data: dict[str, Any],
    ) -> dict[str, Any]:
        merchant = await self._get_merchant(merchant_id)
        document_record = {
            "document_type": document_type,
            "file_url": upload_data["url"],
            "public_id": upload_data["public_id"],
            "original_filename": upload_data.get("original_filename"),
            "file_type": upload_data.get("file_type"),
            "file_size": upload_data.get("file_size"),
        }
        documents = merchant.kyb_data.setdefault("documents", [])
        documents.append(document_record)
        merchant.kyb_data["documents"] = documents
        await merchant.save()
        return success_response(
            status.HTTP_201_CREATED,
            "Document uploaded successfully",
            data={"document": document_record, "documents": documents},
        )

    async def submit(self, merchant_id: UUID) -> dict[str, Any]:
        merchant = await self._get_merchant(merchant_id)
        required = ("business", "address", "verification")
        missing = [step for step in required if step not in merchant.kyb_data]
        if missing:
            raise ErrorResponse(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                f"Complete onboarding steps before submit: {', '.join(missing)}",
            )

        from datetime import UTC, datetime

        merchant.kyb_data["submitted_at"] = datetime.now(UTC).isoformat()
        merchant.status = MerchantStatus.PENDING_KYB
        await merchant.save()
        return success_response(
            status.HTTP_200_OK,
            "KYB submitted for review",
            data={"status": merchant.status, "kyb_data": merchant.kyb_data},
        )

    async def status(self, merchant_id: UUID) -> dict[str, Any]:
        merchant = await self._get_merchant(merchant_id)
        api_keys = await MerchantApiKey.filter(
            merchant_id=merchant_id,
            revoked_at__isnull=True,
        ).all()
        webhook_registered = bool(
            await Merchant.filter(id=merchant_id).exists()
        )
        return success_response(
            status.HTTP_200_OK,
            "Onboarding status retrieved",
            data={
                "merchant_status": merchant.status,
                "kyb_data": merchant.kyb_data,
                "api_key_count": len(api_keys),
                "api_key_prefixes": [key.key_prefix for key in api_keys],
                "webhook_setup_required": webhook_registered,
                "checklist": {
                    "kyb_submitted": bool(merchant.kyb_data.get("submitted_at")),
                    "api_keys_ready": len(api_keys) > 0,
                },
            },
        )

    async def _get_merchant(self, merchant_id: UUID) -> Merchant:
        merchant = await Merchant.get_or_none(id=merchant_id)
        if not merchant:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND, "Merchant not found")
        return merchant


class SettingsService:
    """Settings / API Center for merchant dashboard."""

    async def get_credentials(self, merchant_id: UUID) -> dict[str, Any]:
        merchant = await Merchant.get(id=merchant_id)
        keys = await MerchantApiKey.filter(merchant_id=merchant_id).order_by(
            "-created_at"
        )
        active_key = next((k for k in keys if k.revoked_at is None), None)
        return success_response(
            status.HTTP_200_OK,
            "API credentials retrieved",
            data={
                "public_key": f"pk_{'live' if merchant else 'test'}_wv_{str(merchant.id).replace('-', '')[:16]}",
                "secret_key_prefix": active_key.key_prefix if active_key else None,
                "keys": [
                    {
                        "id": key.id,
                        "prefix": key.key_prefix,
                        "name": key.name,
                        "created_at": key.created_at,
                        "revoked_at": key.revoked_at,
                    }
                    for key in keys
                ],
            },
        )

    async def rotate_credentials(self, merchant_id: UUID) -> dict[str, Any]:
        from datetime import UTC, datetime

        keys = await MerchantApiKey.filter(
            merchant_id=merchant_id,
            revoked_at__isnull=True,
        )
        now = datetime.now(UTC)
        for key in keys:
            key.revoked_at = now
            await key.save()

        raw_key = generate_api_key()
        merchant = await Merchant.get(id=merchant_id)
        new_key = await MerchantApiKey.create(
            id=uuid4(),
            merchant=merchant,
            key_hash=hash_api_key(raw_key),
            key_prefix=api_key_prefix(raw_key),
            name="rotated",
        )
        return success_response(
            status.HTTP_201_CREATED,
            "API key rotated",
            data={
                "api_key": raw_key,
                "key_prefix": new_key.key_prefix,
            },
        )

    async def get_webhook(self, merchant_id: UUID) -> dict[str, Any]:
        from app.models.transactions import WebhookRegistration

        registration = await WebhookRegistration.filter(
            merchant_id=merchant_id,
            active=True,
        ).first()
        if not registration:
            return success_response(
                status.HTTP_200_OK,
                "No webhook configured",
                data=None,
            )
        return success_response(
            status.HTTP_200_OK,
            "Webhook configuration retrieved",
            data={
                "id": registration.id,
                "url": registration.url,
                "events": registration.events,
                "active": registration.active,
                "created_at": registration.created_at,
            },
        )

    async def update_webhook(
        self, merchant_id: UUID, body: Any
    ) -> dict[str, Any]:
        from app.constants import OUTBOUND_EVENTS_ALL
        from app.models.transactions import WebhookRegistration
        from app.schemas.requests.settings import UpdateWebhookSettingsRequestSchema

        if not isinstance(body, UpdateWebhookSettingsRequestSchema):
            body = UpdateWebhookSettingsRequestSchema.model_validate(body)

        events = body.events or OUTBOUND_EVENTS_ALL
        registration = await WebhookRegistration.filter(
            merchant_id=merchant_id,
            active=True,
        ).first()
        if registration:
            registration.url = body.url
            registration.secret = body.secret
            registration.events = events
            registration.active = body.active
            await registration.save()
        else:
            registration = await WebhookRegistration.create(
                id=uuid4(),
                merchant_id=merchant_id,
                url=body.url,
                secret=body.secret,
                events=events,
                active=body.active,
            )

        return success_response(
            status.HTTP_200_OK,
            "Webhook configuration saved",
            data={
                "id": registration.id,
                "url": registration.url,
                "events": registration.events,
                "active": registration.active,
            },
        )

    async def test_webhook(self, merchant_id: UUID) -> dict[str, Any]:
        from app.services.webhook_forwarder import WebhookForwarderService

        forwarder = WebhookForwarderService()
        delivered = await forwarder.emit_test_event(merchant_id)
        return success_response(
            status.HTTP_200_OK,
            "Webhook test dispatched",
            data={"delivered": delivered},
        )

    async def get_profile(self, merchant_id: UUID) -> dict[str, Any]:
        merchant = await Merchant.get(id=merchant_id)
        return success_response(
            status.HTTP_200_OK,
            "Profile retrieved",
            data={
                "name": merchant.name,
                "email": merchant.email,
                "phone": merchant.phone,
                "status": merchant.status,
            },
        )

    async def update_profile(
        self, merchant_id: UUID, body: Any
    ) -> dict[str, Any]:
        from app.schemas.requests.settings import UpdateProfileSettingsRequestSchema

        if not isinstance(body, UpdateProfileSettingsRequestSchema):
            body = UpdateProfileSettingsRequestSchema.model_validate(body)

        merchant = await Merchant.get(id=merchant_id)
        if body.name is not None:
            merchant.name = body.name
        if body.phone is not None:
            merchant.phone = body.phone
        await merchant.save()
        return success_response(
            status.HTTP_200_OK,
            "Profile updated",
            data={
                "name": merchant.name,
                "email": merchant.email,
                "phone": merchant.phone,
            },
        )

    async def change_password(
        self, merchant_id: UUID, body: ChangePasswordRequestSchema
    ) -> dict[str, Any]:
        merchant = await Merchant.get(id=merchant_id)
        if not verify_password(body.current_password, merchant.password_hash):
            raise ErrorResponse(status.HTTP_401_UNAUTHORIZED, "Current password is incorrect")
        merchant.password_hash = hash_password(body.new_password)
        await merchant.save()
        return success_response(
            status.HTTP_200_OK,
            "Password updated",
            data={"updated": True},
        )
