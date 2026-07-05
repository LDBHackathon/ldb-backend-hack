from orjson import loads
from tortoise import fields, migrations
from tortoise.fields.data import JSON_DUMPS
from tortoise.migrations import operations as ops


class Migration(migrations.Migration):
    dependencies = [("main", "0003_merchant_auth_kyb")]

    initial = False

    operations = [
        ops.AddField(
            model_name="ProcessedWebhookEvent",
            name="raw_payload",
            field=fields.JSONField(null=True, default=dict, encoder=JSON_DUMPS, decoder=loads),
        ),
        ops.RunSQL(
            "UPDATE processed_webhook_events SET raw_payload = '{}'::jsonb WHERE raw_payload IS NULL",
            "UPDATE processed_webhook_events SET raw_payload = NULL WHERE raw_payload = '{}'::jsonb",
        ),
        ops.AlterField(
            model_name="ProcessedWebhookEvent",
            name="raw_payload",
            field=fields.JSONField(default=dict, encoder=JSON_DUMPS, decoder=loads),
        ),
    ]
