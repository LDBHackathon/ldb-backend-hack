from typing import Any
from uuid import UUID, uuid4

from fastapi import status

from app.integrations.nomba import NombaVirtualAccountService
from app.models.customers import Customer, DedicatedAccount
from app.schemas.requests.accounts import CreateDedicatedAccountRequestSchema
from app.services.helpers import build_account_response
from app.utils.response_formatter import error_response, success_response


class AccountService:
    """Dedicated virtual account operations."""

    async def create_dedicated(
        self, body: CreateDedicatedAccountRequestSchema, merchant_id: UUID
    ) -> dict[str, Any]:
        customer = await Customer.get_or_none(
            merchant_id=merchant_id,
            merchant_customer_id=body.merchant_customer_id,
        )
        if not customer:
            return error_response(status.HTTP_404_NOT_FOUND, "Customer not found")

        existing = await DedicatedAccount.filter(customer_id=customer.id).first()
        if existing:
            return error_response(
                status.HTTP_409_CONFLICT,
                "Customer already has a dedicated account",
            )

        account_name = body.account_name or customer.name
        nomba_result = await NombaVirtualAccountService.create(
            account_ref=customer.merchant_customer_id,
            account_name=account_name,
        )
        if not nomba_result["success"]:
            return error_response(
                status.HTTP_502_BAD_GATEWAY,
                "Failed to provision Nomba virtual account",
                [str(nomba_result.get("message", "Unknown Nomba error"))],
            )

        va_data = nomba_result["data"] or {}
        account_number = va_data.get("accountNumber") or va_data.get("bankAccountNumber")
        if not account_number:
            return error_response(
                status.HTTP_502_BAD_GATEWAY,
                "Nomba response missing account number",
            )

        account = await DedicatedAccount.create(
            id=uuid4(),
            customer=customer,
            nomba_va_id=va_data.get("id") or va_data.get("accountId"),
            account_number=str(account_number).replace(" ", ""),
            account_name=account_name,
            account_ref=customer.merchant_customer_id,
        )

        return success_response(
            status.HTTP_201_CREATED,
            "Dedicated account created",
            data=await build_account_response(account),
        )

    async def get(self, account_id: UUID, merchant_id: UUID) -> dict[str, Any]:
        account = await DedicatedAccount.get_or_none(id=account_id)
        if not account:
            return error_response(status.HTTP_404_NOT_FOUND, "Account not found")
        await account.fetch_related("customer")
        if account.customer.merchant_id != merchant_id:
            return error_response(status.HTTP_404_NOT_FOUND, "Account not found")

        return success_response(
            status.HTTP_200_OK,
            "Account retrieved",
            data=await build_account_response(account),
        )
