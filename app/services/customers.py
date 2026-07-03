from typing import Any
from uuid import UUID, uuid4

from fastapi import status

from app.integrations.nomba import NombaVirtualAccountService
from app.models.customers import Customer, DedicatedAccount
from app.schemas.requests.customers import (
    CreateCustomerRequestSchema,
    UpdateCustomerRequestSchema,
)
from app.services.helpers import build_customer_response
from app.utils.response_formatter import error_response, success_response


class CustomerService:
    """Customer profile and wallet management."""

    async def create(
        self, body: CreateCustomerRequestSchema, merchant_id: UUID
    ) -> dict[str, Any]:
        existing = await Customer.get_or_none(
            merchant_id=merchant_id,
            merchant_customer_id=body.merchant_customer_id,
        )
        if existing:
            return error_response(
                status.HTTP_409_CONFLICT,
                "Customer with this merchant_customer_id already exists",
            )

        existing_account = await DedicatedAccount.filter(
            account_ref=body.merchant_customer_id
        ).first()
        if existing_account:
            return error_response(
                status.HTTP_409_CONFLICT,
                "Dedicated account reference already exists",
            )

        customer = await Customer.create(
            id=uuid4(),
            merchant_id=merchant_id,
            merchant_customer_id=body.merchant_customer_id,
            name=body.name,
            email=body.email,
            phone=body.phone,
            target_amount=body.target_amount,
            metadata=body.metadata,
        )

        nomba_result = await NombaVirtualAccountService.create(
            account_ref=body.merchant_customer_id,
            account_name=body.name,
        )
        if not nomba_result["success"]:
            await customer.delete()
            return error_response(
                status.HTTP_502_BAD_GATEWAY,
                "Failed to provision Nomba virtual account",
                [str(nomba_result.get("message", "Unknown Nomba error"))],
            )

        va_data = nomba_result["data"] or {}
        account_number = va_data.get("accountNumber") or va_data.get("bankAccountNumber")
        if not account_number:
            await customer.delete()
            return error_response(
                status.HTTP_502_BAD_GATEWAY,
                "Nomba response missing account number",
            )

        await DedicatedAccount.create(
            id=uuid4(),
            customer=customer,
            nomba_va_id=va_data.get("id") or va_data.get("accountId"),
            account_number=str(account_number).replace(" ", ""),
            account_name=body.name,
            account_ref=body.merchant_customer_id,
        )

        return success_response(
            status.HTTP_201_CREATED,
            "Customer and dedicated account created",
            data=await build_customer_response(customer),
        )

    async def get(self, customer_id: str, merchant_id: UUID) -> dict[str, Any]:
        customer = await self._resolve_customer(customer_id, merchant_id)
        if not customer:
            return error_response(status.HTTP_404_NOT_FOUND, "Customer not found")
        return success_response(
            status.HTTP_200_OK,
            "Customer retrieved",
            data=await build_customer_response(customer),
        )

    async def update(
        self,
        customer_id: str,
        body: UpdateCustomerRequestSchema,
        merchant_id: UUID,
    ) -> dict[str, Any]:
        customer = await self._resolve_customer(customer_id, merchant_id)
        if not customer:
            return error_response(status.HTTP_404_NOT_FOUND, "Customer not found")

        if body.name is not None:
            customer.name = body.name
        if body.email is not None:
            customer.email = body.email
        if body.phone is not None:
            customer.phone = body.phone
        if body.target_amount is not None:
            customer.target_amount = body.target_amount
        if body.metadata is not None:
            customer.metadata = body.metadata

        await customer.save()

        if body.name is not None:
            account = await DedicatedAccount.filter(customer_id=customer.id).first()
            if account:
                account.account_name = body.name
                await account.save()
                await NombaVirtualAccountService.update_account_name(
                    account.account_ref, body.name
                )

        return success_response(
            status.HTTP_200_OK,
            "Customer updated",
            data=await build_customer_response(customer),
        )

    async def _resolve_customer(
        self, customer_id: str, merchant_id: UUID
    ) -> Customer | None:
        try:
            parsed_id = UUID(customer_id)
            customer = await Customer.get_or_none(id=parsed_id, merchant_id=merchant_id)
            if customer:
                return customer
        except ValueError:
            pass
        return await Customer.get_or_none(
            merchant_id=merchant_id,
            merchant_customer_id=customer_id,
        )
