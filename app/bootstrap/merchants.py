"""One-time bootstrap for legacy env-based merchant credentials."""

from uuid import UUID, uuid4

from app.enums.customer import CustomerStatus
from app.enums.merchant import MerchantStatus
from app.models.customers import Customer, DedicatedAccount
from app.models.merchants import Merchant, MerchantApiKey
from app.settings import settings
from app.utils.api_keys import api_key_prefix, hash_api_key
from app.utils.logger import logger


async def bootstrap_default_merchant() -> None:
    """Seed default merchant + API key from env for existing deployments."""
    if not settings.LDB_API_KEY or not settings.DEFAULT_MERCHANT_ID:
        return

    merchant_id = UUID(settings.DEFAULT_MERCHANT_ID)
    merchant = await Merchant.get_or_none(id=merchant_id)
    if merchant is None:
        merchant = await Merchant.create(
            id=merchant_id,
            name="Default Merchant",
            email=f"bootstrap-{merchant_id}@ldb.local",
            status=MerchantStatus.ACTIVE,
        )
        logger.info("Bootstrap merchant created", merchant_id=str(merchant_id))

    prefix = api_key_prefix(settings.LDB_API_KEY)
    key_hash = hash_api_key(settings.LDB_API_KEY)
    existing_key = await MerchantApiKey.get_or_none(
        merchant_id=merchant_id,
        key_prefix=prefix,
        key_hash=key_hash,
    )
    if existing_key is None:
        await MerchantApiKey.create(
            id=uuid4(),
            merchant=merchant,
            key_hash=key_hash,
            key_prefix=prefix,
            name="bootstrap",
        )
        logger.info("Bootstrap API key seeded", merchant_id=str(merchant_id))

    customers_with_accounts = await Customer.filter(
        merchant_id=merchant_id,
        nomba_sub_account_id__isnull=True,
    ).all()
    for customer in customers_with_accounts:
        account = await DedicatedAccount.filter(customer_id=customer.id).first()
        if account:
            customer.status = CustomerStatus.ACTIVE
            await customer.save()
