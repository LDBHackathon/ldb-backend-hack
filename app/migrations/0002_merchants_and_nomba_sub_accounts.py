from tortoise import migrations
from tortoise.migrations import operations as ops
from app.enums.customer import CustomerStatus
from app.enums.merchant import MerchantStatus
from tortoise.fields.base import OnDelete
from uuid import uuid4
from tortoise import fields
from tortoise.indexes import Index

class Migration(migrations.Migration):
    dependencies = [('main', '0001_initial')]

    initial = False

    operations = [
        ops.CreateModel(
            name='Merchant',
            fields=[
                ('id', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True)),
                ('name', fields.CharField(max_length=200)),
                ('email', fields.CharField(unique=True, max_length=200)),
                ('status', fields.CharEnumField(default=MerchantStatus.ACTIVE, description='ACTIVE: active\nSUSPENDED: suspended', enum_type=MerchantStatus, max_length=9)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'merchants', 'app': 'main', 'pk_attr': 'id', 'table_description': 'Business registered on LDB.'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='MerchantApiKey',
            fields=[
                ('id', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True)),
                ('merchant', fields.ForeignKeyField('main.Merchant', source_field='merchant_id', db_constraint=True, to_field='id', related_name='api_keys', on_delete=OnDelete.CASCADE)),
                ('key_hash', fields.CharField(max_length=64)),
                ('key_prefix', fields.CharField(db_index=True, max_length=32)),
                ('name', fields.CharField(default='default', max_length=100)),
                ('revoked_at', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'merchant_api_keys', 'app': 'main', 'indexes': [Index(fields=['key_prefix', 'key_hash'])], 'pk_attr': 'id', 'table_description': 'Hashed API key issued to a merchant.'},
            bases=['Model'],
        ),
        ops.AddField(
            model_name='Customer',
            name='nomba_sub_account_id',
            field=fields.CharField(null=True, max_length=100),
        ),
        ops.AddField(
            model_name='Customer',
            name='nomba_sub_account_ref',
            field=fields.CharField(null=True, max_length=100),
        ),
        ops.AddField(
            model_name='Customer',
            name='status',
            field=fields.CharEnumField(null=True, default=CustomerStatus.PENDING_NOMBA, description='ACTIVE: active\nPENDING_NOMBA: pending_nomba\nSUSPENDED: suspended', enum_type=CustomerStatus, max_length=13),
        ),
        ops.RunSQL(
            "UPDATE customers SET status = 'active' WHERE status IS NULL",
            "UPDATE customers SET status = NULL WHERE status = 'active'",
        ),
        ops.AlterField(
            model_name='Customer',
            name='status',
            field=fields.CharEnumField(default=CustomerStatus.PENDING_NOMBA, description='ACTIVE: active\nPENDING_NOMBA: pending_nomba\nSUSPENDED: suspended', enum_type=CustomerStatus, max_length=13),
        ),
        ops.AddField(
            model_name='DedicatedAccount',
            name='nomba_sub_account_id',
            field=fields.CharField(null=True, max_length=100),
        ),
    ]
