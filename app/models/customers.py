from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from tortoise import fields, models

from app.enums.account import AccountStatus
from app.enums.customer import CustomerStatus


class Customer(models.Model):
    """Merchant customer with a persistent wallet balance."""

    id: UUID = fields.UUIDField(primary_key=True)
    merchant_id: UUID = fields.UUIDField()
    merchant_customer_id: str = fields.CharField(max_length=100)
    name: str = fields.CharField(max_length=200)
    email: str | None = fields.CharField(max_length=200, null=True)
    phone: str | None = fields.CharField(max_length=50, null=True)
    target_amount: Decimal | None = fields.DecimalField(
        max_digits=30, decimal_places=2, null=True
    )
    wallet_balance: Decimal = fields.DecimalField(
        max_digits=30, decimal_places=2, default=Decimal("0")
    )
    nomba_sub_account_id: str | None = fields.CharField(max_length=100, null=True)
    nomba_sub_account_ref: str | None = fields.CharField(max_length=100, null=True)
    status: CustomerStatus = fields.CharEnumField(
        CustomerStatus, default=CustomerStatus.PENDING_NOMBA
    )
    metadata = fields.JSONField[dict[str, Any]](default=dict)
    created_at: datetime = fields.DatetimeField(auto_now_add=True)
    updated_at: datetime = fields.DatetimeField(auto_now=True)

    class Meta(models.Model.Meta):
        table = "customers"
        unique_together = (("merchant_id", "merchant_customer_id"),)
        indexes = (("merchant_customer_id",),)


class DedicatedAccount(models.Model):
    """Nomba-backed dedicated virtual account."""

    id: UUID = fields.UUIDField(primary_key=True)
    customer: fields.ForeignKeyRelation[Customer] = fields.ForeignKeyField(
        "main.Customer", related_name="dedicated_accounts"
    )
    nomba_va_id: str | None = fields.CharField(max_length=100, null=True)
    nomba_sub_account_id: str | None = fields.CharField(max_length=100, null=True)
    account_number: str = fields.CharField(max_length=20, unique=True)
    account_name: str = fields.CharField(max_length=200)
    account_ref: str = fields.CharField(max_length=100, unique=True)
    status: AccountStatus = fields.CharEnumField(
        AccountStatus, default=AccountStatus.ACTIVE
    )
    created_at: datetime = fields.DatetimeField(auto_now_add=True)
    updated_at: datetime = fields.DatetimeField(auto_now=True)

    class Meta(models.Model.Meta):
        table = "dedicated_accounts"
        indexes = (("account_number",), ("account_ref",))
