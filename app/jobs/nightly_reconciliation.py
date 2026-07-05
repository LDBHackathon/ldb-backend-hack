from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from app.constants import (
    RECONCILIATION_SAFETY_NET_MATCH,
    RECONCILIATION_SAFETY_NET_MISSING,
)
from app.integrations.nomba.transactions import NombaTransactionService
from app.models.customers import Customer
from app.models.transactions import ReconciliationLog, Transaction
from app.utils.logger import logger


async def _reconcile_nomba_items(nomba_items: list) -> tuple[int, int]:
    matched = 0
    missing = 0

    for item in nomba_items:
        if not isinstance(item, dict):
            continue
        nomba_tx_id = item.get("id") or item.get("transactionId")
        merchant_tx_ref = item.get("merchantTxRef")
        if not nomba_tx_id and not merchant_tx_ref:
            continue

        local_tx = None
        if nomba_tx_id:
            local_tx = await Transaction.get_or_none(nomba_transaction_id=nomba_tx_id)
        if local_tx is None and merchant_tx_ref:
            local_tx = await Transaction.get_or_none(merchant_tx_ref=merchant_tx_ref)

        if local_tx is None:
            missing += 1
            logger.warning(
                "Nightly reconciliation missing local transaction",
                nomba_transaction_id=nomba_tx_id,
                merchant_tx_ref=merchant_tx_ref,
            )
            continue

        matched += 1
        await ReconciliationLog.create(
            id=uuid4(),
            transaction=local_tx,
            expected_amount=local_tx.amount,
            received_amount=local_tx.amount,
            decision=RECONCILIATION_SAFETY_NET_MATCH,
            details={
                "nomba_transaction_id": nomba_tx_id,
                "checked_at": datetime.now(UTC).isoformat(),
            },
        )

    return matched, missing


async def run_nightly_reconciliation() -> None:
    """Compare Nomba transactions against the local ledger per customer sub-account."""
    logger.info("Nightly reconciliation started")
    end_date = date.today()
    start_date = end_date - timedelta(days=1)

    customers = await Customer.filter(nomba_sub_account_id__isnull=False).all()
    sub_account_ids = {c.nomba_sub_account_id for c in customers if c.nomba_sub_account_id}

    total_matched = 0
    total_missing = 0

    if sub_account_ids:
        for sub_account_id in sub_account_ids:
            result = await NombaTransactionService.list_transactions(
                start_date=start_date,
                end_date=end_date,
                limit=200,
                sub_account_id=sub_account_id,
            )
            if not result["success"]:
                logger.warning(
                    "Nightly reconciliation skipped for sub-account",
                    sub_account_id=sub_account_id,
                    message=result.get("message"),
                )
                continue

            nomba_items = result["data"]
            if isinstance(nomba_items, dict):
                nomba_items = nomba_items.get("results") or nomba_items.get("items") or []

            if not isinstance(nomba_items, list):
                logger.warning(
                    "Nightly reconciliation skipped: unexpected Nomba payload",
                    sub_account_id=sub_account_id,
                )
                continue

            matched, missing = await _reconcile_nomba_items(nomba_items)
            total_matched += matched
            total_missing += missing
    else:
        result = await NombaTransactionService.list_transactions(
            start_date=start_date,
            end_date=end_date,
            limit=200,
        )
        if not result["success"]:
            logger.warning(
                "Nightly reconciliation skipped: Nomba fetch failed",
                message=result.get("message"),
            )
            return

        nomba_items = result["data"]
        if isinstance(nomba_items, dict):
            nomba_items = nomba_items.get("results") or nomba_items.get("items") or []

        if not isinstance(nomba_items, list):
            logger.warning("Nightly reconciliation skipped: unexpected Nomba payload")
            return

        total_matched, total_missing = await _reconcile_nomba_items(nomba_items)

    logger.info(
        "Nightly reconciliation completed",
        matched=total_matched,
        missing=total_missing,
        sub_accounts=len(sub_account_ids),
        decision_missing=RECONCILIATION_SAFETY_NET_MISSING if total_missing else None,
    )
