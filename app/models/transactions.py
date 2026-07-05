from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from tortoise import fields, models

from app.enums.transaction import TransactionStatus, TransactionType


class Transaction(models.Model):
    """Inbound transfer tied to a dedicated account."""

    id: UUID = fields.UUIDField(primary_key=True)
    dedicated_account: fields.ForeignKeyRelation | None = fields.ForeignKeyField(
        "main.DedicatedAccount",
        related_name="transactions",
        null=True,
    )
    nomba_request_id: str = fields.CharField(max_length=100, unique=True)
    nomba_transaction_id: str | None = fields.CharField(max_length=200, null=True)
    merchant_tx_ref: str | None = fields.CharField(max_length=200, null=True)
    amount: Decimal = fields.DecimalField(max_digits=30, decimal_places=2)
    fee: Decimal = fields.DecimalField(max_digits=30, decimal_places=2, default=0)
    sender_name: str | None = fields.CharField(max_length=200, null=True)
    sender_bank: str | None = fields.CharField(max_length=200, null=True)
    type: TransactionType = fields.CharEnumField(
        TransactionType, default=TransactionType.INBOUND
    )
    status: TransactionStatus = fields.CharEnumField(TransactionStatus)
    narration: str | None = fields.CharField(max_length=500, null=True)
    raw_payload = fields.JSONField[dict[str, Any]](default=dict)
    created_at: datetime = fields.DatetimeField(auto_now_add=True)

    class Meta(models.Model.Meta):
        table = "transactions"
        indexes = (("nomba_transaction_id",), ("merchant_tx_ref",))


class SuspenseLog(models.Model):
    """Quarantined or misdirected funds."""

    id: UUID = fields.UUIDField(primary_key=True)
    transaction: fields.ForeignKeyRelation[Transaction] = fields.ForeignKeyField(
        "main.Transaction", related_name="suspense_logs"
    )
    reason: str = fields.CharField(max_length=100)
    amount: Decimal = fields.DecimalField(max_digits=30, decimal_places=2)
    resolved: bool = fields.BooleanField(default=False)
    resolved_at: datetime | None = fields.DatetimeField(null=True)
    created_at: datetime = fields.DatetimeField(auto_now_add=True)

    class Meta(models.Model.Meta):
        table = "suspense_logs"


class ReconciliationLog(models.Model):
    """Audit trail for reconciliation decisions."""

    id: UUID = fields.UUIDField(primary_key=True)
    transaction: fields.ForeignKeyRelation[Transaction] = fields.ForeignKeyField(
        "main.Transaction", related_name="reconciliation_logs"
    )
    expected_amount: Decimal | None = fields.DecimalField(
        max_digits=30, decimal_places=2, null=True
    )
    received_amount: Decimal = fields.DecimalField(max_digits=30, decimal_places=2)
    decision: str = fields.CharField(max_length=100)
    details = fields.JSONField[dict[str, Any]](default=dict)
    created_at: datetime = fields.DatetimeField(auto_now_add=True)

    class Meta(models.Model.Meta):
        table = "reconciliation_logs"


class WebhookRegistration(models.Model):
    """Merchant webhook subscription."""

    id: UUID = fields.UUIDField(primary_key=True)
    merchant_id: UUID = fields.UUIDField()
    url: str = fields.CharField(max_length=500)
    secret: str = fields.CharField(max_length=255)
    events = fields.JSONField[list[str]](default=list)
    active: bool = fields.BooleanField(default=True)
    created_at: datetime = fields.DatetimeField(auto_now_add=True)

    class Meta(models.Model.Meta):
        table = "webhook_registrations"


class ProcessedWebhookEvent(models.Model):
    """Idempotency ledger for inbound Nomba webhooks."""

    id: UUID = fields.UUIDField(primary_key=True)
    request_id: str = fields.CharField(max_length=100, unique=True)
    event_type: str = fields.CharField(max_length=100)
    raw_payload = fields.JSONField[dict[str, Any]](default=dict)
    processed_at: datetime = fields.DatetimeField(auto_now_add=True)

    class Meta(models.Model.Meta):
        table = "processed_webhook_events"
