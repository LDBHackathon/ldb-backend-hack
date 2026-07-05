from datetime import datetime
from typing import Any
from uuid import UUID

from tortoise import fields, models

from app.enums.merchant import MerchantStatus


class Merchant(models.Model):
    """Business registered on LDB."""

    id: UUID = fields.UUIDField(primary_key=True)
    name: str = fields.CharField(max_length=200)
    email: str = fields.CharField(max_length=200, unique=True)
    phone: str | None = fields.CharField(max_length=50, null=True)
    password_hash: str | None = fields.CharField(max_length=255, null=True)
    kyb_data = fields.JSONField[dict[str, Any]](default=dict)
    status: MerchantStatus = fields.CharEnumField(
        MerchantStatus, default=MerchantStatus.PENDING_KYB
    )
    created_at: datetime = fields.DatetimeField(auto_now_add=True)
    updated_at: datetime = fields.DatetimeField(auto_now=True)

    class Meta(models.Model.Meta):
        table = "merchants"


class MerchantApiKey(models.Model):
    """Hashed API key issued to a merchant."""

    id: UUID = fields.UUIDField(primary_key=True)
    merchant: fields.ForeignKeyRelation[Merchant] = fields.ForeignKeyField(
        "main.Merchant", related_name="api_keys"
    )
    key_hash: str = fields.CharField(max_length=64)
    key_prefix: str = fields.CharField(max_length=32, index=True)
    name: str = fields.CharField(max_length=100, default="default")
    revoked_at: datetime | None = fields.DatetimeField(null=True)
    created_at: datetime = fields.DatetimeField(auto_now_add=True)

    class Meta(models.Model.Meta):
        table = "merchant_api_keys"
        indexes = (("key_prefix", "key_hash"),)
