from tortoise import migrations
from tortoise.migrations import operations as ops
from app.enums.account import AccountStatus
from app.enums.transaction import TransactionStatus, TransactionType
from decimal import Decimal
from orjson import loads
from tortoise.fields.base import OnDelete
from tortoise.fields.data import JSON_DUMPS
from uuid import uuid4
from tortoise import fields
from tortoise.indexes import Index

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='Customer',
            fields=[
                ('id', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True)),
                ('merchant_id', fields.UUIDField()),
                ('merchant_customer_id', fields.CharField(max_length=100)),
                ('name', fields.CharField(max_length=200)),
                ('email', fields.CharField(null=True, max_length=200)),
                ('phone', fields.CharField(null=True, max_length=50)),
                ('target_amount', fields.DecimalField(null=True, max_digits=30, decimal_places=2)),
                ('wallet_balance', fields.DecimalField(default=Decimal('0'), max_digits=30, decimal_places=2)),
                ('metadata', fields.JSONField(default=dict, encoder=JSON_DUMPS, decoder=loads)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'customers', 'app': 'main', 'unique_together': (('merchant_id', 'merchant_customer_id'),), 'indexes': [Index(fields=['merchant_customer_id'])], 'pk_attr': 'id', 'table_description': 'Merchant customer with a persistent wallet balance.'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='DedicatedAccount',
            fields=[
                ('id', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True)),
                ('customer', fields.ForeignKeyField('main.Customer', source_field='customer_id', db_constraint=True, to_field='id', related_name='dedicated_accounts', on_delete=OnDelete.CASCADE)),
                ('nomba_va_id', fields.CharField(null=True, max_length=100)),
                ('account_number', fields.CharField(unique=True, max_length=20)),
                ('account_name', fields.CharField(max_length=200)),
                ('account_ref', fields.CharField(unique=True, max_length=100)),
                ('status', fields.CharEnumField(default=AccountStatus.ACTIVE, description='ACTIVE: active\nCLOSED: closed\nSUSPENDED: suspended', enum_type=AccountStatus, max_length=9)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'dedicated_accounts', 'app': 'main', 'indexes': [Index(fields=['account_number']), Index(fields=['account_ref'])], 'pk_attr': 'id', 'table_description': 'Nomba-backed dedicated virtual account.'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='ProcessedWebhookEvent',
            fields=[
                ('id', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True)),
                ('request_id', fields.CharField(unique=True, max_length=100)),
                ('event_type', fields.CharField(max_length=100)),
                ('processed_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'processed_webhook_events', 'app': 'main', 'pk_attr': 'id', 'table_description': 'Idempotency ledger for inbound Nomba webhooks.'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Transaction',
            fields=[
                ('id', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True)),
                ('dedicated_account', fields.ForeignKeyField('main.DedicatedAccount', source_field='dedicated_account_id', null=True, db_constraint=True, to_field='id', related_name='transactions', on_delete=OnDelete.CASCADE)),
                ('nomba_request_id', fields.CharField(unique=True, max_length=100)),
                ('nomba_transaction_id', fields.CharField(null=True, max_length=200)),
                ('merchant_tx_ref', fields.CharField(null=True, max_length=200)),
                ('amount', fields.DecimalField(max_digits=30, decimal_places=2)),
                ('fee', fields.DecimalField(default=0, max_digits=30, decimal_places=2)),
                ('sender_name', fields.CharField(null=True, max_length=200)),
                ('sender_bank', fields.CharField(null=True, max_length=200)),
                ('type', fields.CharEnumField(default=TransactionType.INBOUND, description='INBOUND: inbound', enum_type=TransactionType, max_length=7)),
                ('status', fields.CharEnumField(description='FULL: full\nPARTIAL: partial\nOVERPAYMENT: overpayment\nMISDIRECTED: misdirected', enum_type=TransactionStatus, max_length=11)),
                ('narration', fields.CharField(null=True, max_length=500)),
                ('raw_payload', fields.JSONField(default=dict, encoder=JSON_DUMPS, decoder=loads)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'transactions', 'app': 'main', 'indexes': [Index(fields=['nomba_transaction_id']), Index(fields=['merchant_tx_ref'])], 'pk_attr': 'id', 'table_description': 'Inbound transfer tied to a dedicated account.'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='ReconciliationLog',
            fields=[
                ('id', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True)),
                ('transaction', fields.ForeignKeyField('main.Transaction', source_field='transaction_id', db_constraint=True, to_field='id', related_name='reconciliation_logs', on_delete=OnDelete.CASCADE)),
                ('expected_amount', fields.DecimalField(null=True, max_digits=30, decimal_places=2)),
                ('received_amount', fields.DecimalField(max_digits=30, decimal_places=2)),
                ('decision', fields.CharField(max_length=100)),
                ('details', fields.JSONField(default=dict, encoder=JSON_DUMPS, decoder=loads)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'reconciliation_logs', 'app': 'main', 'pk_attr': 'id', 'table_description': 'Audit trail for reconciliation decisions.'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='SuspenseLog',
            fields=[
                ('id', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True)),
                ('transaction', fields.ForeignKeyField('main.Transaction', source_field='transaction_id', db_constraint=True, to_field='id', related_name='suspense_logs', on_delete=OnDelete.CASCADE)),
                ('reason', fields.CharField(max_length=100)),
                ('amount', fields.DecimalField(max_digits=30, decimal_places=2)),
                ('resolved', fields.BooleanField(default=False)),
                ('resolved_at', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'suspense_logs', 'app': 'main', 'pk_attr': 'id', 'table_description': 'Quarantined or misdirected funds.'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='WebhookRegistration',
            fields=[
                ('id', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True)),
                ('merchant_id', fields.UUIDField()),
                ('url', fields.CharField(max_length=500)),
                ('secret', fields.CharField(max_length=255)),
                ('events', fields.JSONField(default=list, encoder=JSON_DUMPS, decoder=loads)),
                ('active', fields.BooleanField(default=True)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'webhook_registrations', 'app': 'main', 'pk_attr': 'id', 'table_description': 'Merchant webhook subscription.'},
            bases=['Model'],
        ),
    ]
