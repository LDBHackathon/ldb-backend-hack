from typing import Any
from uuid import UUID, uuid4

from fastapi import status

from app.enums.customer import CustomerStatus
from app.integrations.nomba import NombaVirtualAccountService
from app.integrations.nomba.helpers import build_nomba_account_ref
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
            id=body.customer_id,
            merchant_id=merchant_id,
        )
        if not customer:
            return error_response(status.HTTP_404_NOT_FOUND, "Customer not found")

        if not customer.nomba_sub_account_id:
            return error_response(
                status.HTTP_409_CONFLICT,
                "Customer has no Nomba sub-account; link one before creating a dedicated account",
            )

        if customer.status != CustomerStatus.ACTIVE:
            return error_response(
                status.HTTP_409_CONFLICT,
                "Customer Nomba provisioning is incomplete",
            )

        existing = await DedicatedAccount.filter(customer_id=customer.id).first()
        if existing:
            return error_response(
                status.HTTP_409_CONFLICT,
                "Customer already has a dedicated account",
            )

        account_name = body.account_name or customer.name
        account_ref = build_nomba_account_ref()
        nomba_result = await NombaVirtualAccountService.create(
            account_ref=account_ref,
            account_name=account_name,
            sub_account_id=customer.nomba_sub_account_id,
            expected_amount=customer.target_amount,
        )
        if not nomba_result["success"]:
            status_code = nomba_result.get("status_code", status.HTTP_502_BAD_GATEWAY)
            http_status = (
                status.HTTP_400_BAD_REQUEST
                if status_code == 400
                else status.HTTP_502_BAD_GATEWAY
            )
            return error_response(
                http_status,
                "Failed to provision Nomba virtual account",
                [str(nomba_result.get("message", "Unknown Nomba error"))],
            )

        va_data = nomba_result["data"] or {}
        account_number = va_data.get("account_number")
        if not account_number:
            return error_response(
                status.HTTP_502_BAD_GATEWAY,
                "Nomba response missing bank account number",
            )

        account = await DedicatedAccount.create(
            id=uuid4(),
            customer=customer,
            nomba_va_id=va_data.get("nomba_va_id"),
            nomba_sub_account_id=customer.nomba_sub_account_id,
            account_number=account_number,
            account_name=account_name,
            account_ref=va_data.get("account_ref") or account_ref,
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
