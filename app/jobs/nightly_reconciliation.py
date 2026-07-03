from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from app.constants import (
    RECONCILIATION_SAFETY_NET_MATCH,
    RECONCILIATION_SAFETY_NET_MISSING,
)
from app.integrations.nomba.transactions import NombaTransactionService
from app.models.transactions import ReconciliationLog, Transaction
from app.utils.logger import logger


async def run_nightly_reconciliation() -> None:
    """Compare Nomba transactions against the local ledger."""
    logger.info("Nightly reconciliation started")
    end_date = date.today()
    start_date = end_date - timedelta(days=1)

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

    matched = 0
    missing = 0

    for item in nomba_items:
        if not isinstance(item, dict):
            continue
        nomba_tx_id = item.get("transactionId") or item.get("id")
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
            details={"nomba_transaction_id": nomba_tx_id, "checked_at": datetime.now(UTC).isoformat()},
        )

    logger.info(
        "Nightly reconciliation completed",
        matched=matched,
        missing=missing,
        decision_missing=RECONCILIATION_SAFETY_NET_MISSING if missing else None,
    )
