from typing import Any
from uuid import UUID, uuid4

from fastapi import status

from app.enums.merchant import MerchantStatus
from app.models.merchants import Merchant, MerchantApiKey
from app.schemas.requests.merchants import RegisterMerchantRequestSchema
from app.utils.api_keys import api_key_prefix, generate_api_key, hash_api_key
from app.utils.exceptions import ErrorResponse
from app.utils.response_formatter import success_response


class MerchantService:
    """LDB merchant registration and profile."""

    async def register(self, body: RegisterMerchantRequestSchema) -> dict[str, Any]:
        if await Merchant.filter(email=body.email).exists():
            raise ErrorResponse(
                status.HTTP_409_CONFLICT,
                "A merchant with this email already exists",
            )

        merchant = await Merchant.create(
            id=uuid4(),
            name=body.name,
            email=body.email,
            status=MerchantStatus.ACTIVE,
        )
        raw_key = generate_api_key()
        await MerchantApiKey.create(
            id=uuid4(),
            merchant=merchant,
            key_hash=hash_api_key(raw_key),
            key_prefix=api_key_prefix(raw_key),
        )

        return success_response(
            status.HTTP_201_CREATED,
            "Merchant registered",
            data={
                "merchant": {
                    "id": merchant.id,
                    "name": merchant.name,
                    "email": merchant.email,
                    "status": merchant.status,
                    "created_at": merchant.created_at,
                    "updated_at": merchant.updated_at,
                },
                "api_key": raw_key,
            },
        )

    async def get_profile(self, merchant_id: UUID) -> dict[str, Any]:
        merchant = await Merchant.get_or_none(id=merchant_id)
        if not merchant:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND, "Merchant not found")

        return success_response(
            status.HTTP_200_OK,
            "Merchant profile retrieved",
            data={
                "id": merchant.id,
                "name": merchant.name,
                "email": merchant.email,
                "status": merchant.status,
                "created_at": merchant.created_at,
                "updated_at": merchant.updated_at,
            },
        )
