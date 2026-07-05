from tortoise import migrations
from tortoise.migrations import operations as ops
from app.enums.merchant import MerchantStatus
from orjson import loads
from tortoise.fields.data import JSON_DUMPS
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('main', '0002_merchants_and_nomba_sub_accounts')]

    initial = False

    operations = [
        ops.AlterField(
            model_name='Merchant',
            name='status',
            field=fields.CharEnumField(default=MerchantStatus.PENDING_KYB, description='PENDING_KYB: pending_kyb\nACTIVE: active\nSUSPENDED: suspended', enum_type=MerchantStatus, max_length=11),
        ),
        ops.AddField(
            model_name='Merchant',
            name='kyb_data',
            field=fields.JSONField(null=True, default=dict, encoder=JSON_DUMPS, decoder=loads),
        ),
        ops.RunSQL(
            "UPDATE merchants SET kyb_data = '{}'::jsonb WHERE kyb_data IS NULL",
            "UPDATE merchants SET kyb_data = NULL WHERE kyb_data = '{}'::jsonb",
        ),
        ops.AlterField(
            model_name='Merchant',
            name='kyb_data',
            field=fields.JSONField(default=dict, encoder=JSON_DUMPS, decoder=loads),
        ),
        ops.AddField(
            model_name='Merchant',
            name='password_hash',
            field=fields.CharField(null=True, max_length=255),
        ),
        ops.AddField(
            model_name='Merchant',
            name='phone',
            field=fields.CharField(null=True, max_length=50),
        ),
        ops.RunSQL(
            "UPDATE merchants SET status = 'active' WHERE status IS NULL OR status = 'pending_kyb'",
            "UPDATE merchants SET status = 'pending_kyb' WHERE status = 'active'",
        ),
    ]
