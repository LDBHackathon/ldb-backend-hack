from typing import Any
from uuid import UUID, uuid4

from fastapi import status

from app.enums.customer import CustomerStatus
from app.integrations.nomba import NombaSubAccountService, NombaVirtualAccountService
from app.integrations.nomba.helpers import build_nomba_account_ref
from app.models.customers import Customer, DedicatedAccount
from app.schemas.requests.customers import (
    CreateCustomerRequestSchema,
    LinkNombaSubAccountRequestSchema,
    UpdateCustomerRequestSchema,
)
from app.services.helpers import build_customer_response
from app.utils.logger import logger
from app.utils.references import generate_merchant_customer_id
from app.utils.response_formatter import error_response, success_response


class CustomerService:
    """Customer profile and wallet management."""

    async def create(
        self, body: CreateCustomerRequestSchema, merchant_id: UUID
    ) -> dict[str, Any]:
        merchant_customer_id = generate_merchant_customer_id()
        sub_account_ref = build_nomba_account_ref()

        customer = await Customer.create(
            id=uuid4(),
            merchant_id=merchant_id,
            merchant_customer_id=merchant_customer_id,
            name=body.name,
            email=body.email,
            phone=body.phone,
            target_amount=body.target_amount,
            metadata=body.metadata,
            nomba_sub_account_ref=sub_account_ref,
            status=CustomerStatus.PENDING_NOMBA,
        )
        print(
            "[CUSTOMER_CREATE][START]",
            {
                "customer_id": str(customer.id),
                "merchant_id": str(merchant_id),
                "merchant_customer_id": merchant_customer_id,
                "sub_account_ref": sub_account_ref,
                "name": body.name,
            },
        )

        sub_result = await NombaSubAccountService.create(
            account_name=body.name,
            account_ref=sub_account_ref,
        )
        print(
            "[CUSTOMER_CREATE][SUB_ACCOUNT_RESULT]",
            {
                "customer_id": str(customer.id),
                "success": sub_result.get("success"),
                "status_code": sub_result.get("status_code"),
                "message": sub_result.get("message"),
            },
        )
        if not sub_result["success"]:
            print(
                "[CUSTOMER_CREATE][FALLBACK_NO_SUB_ACCOUNT]",
                {
                    "customer_id": str(customer.id),
                    "reason": "sub-account creation failed",
                    "next_action": "link Nomba sub-account later via /customers/{customer_id}/link-nomba-sub-account",
                },
            )
            return success_response(
                status.HTTP_201_CREATED,
                "Customer created; link Nomba sub-account to complete provisioning",
                data=await build_customer_response(customer),
            )

        sub_data = sub_result["data"] or {}
        sub_account_id = sub_data.get("account_id")
        if not sub_account_id:
            print(
                "[CUSTOMER_CREATE][FALLBACK_MISSING_SUB_ACCOUNT_ID]",
                {
                    "customer_id": str(customer.id),
                    "sub_result_data": sub_data,
                },
            )
            return success_response(
                status.HTTP_201_CREATED,
                "Customer created; Nomba sub-account response missing account ID",
                data=await build_customer_response(customer),
            )

        customer.nomba_sub_account_id = sub_account_id
        await customer.save()
        print(
            "[CUSTOMER_CREATE][SUB_ACCOUNT_LINKED]",
            {
                "customer_id": str(customer.id),
                "nomba_sub_account_id": sub_account_id,
            },
        )

        provisioned = await self._provision_virtual_account(customer, body)
        print(
            "[CUSTOMER_CREATE][VA_PROVISION_RESULT]",
            {
                "customer_id": str(customer.id),
                "success": not bool(provisioned.get("error")),
                "error": provisioned.get("error"),
                "detail": provisioned.get("detail"),
            },
        )
        if provisioned.get("error"):
            logger.warning(
                "Virtual account provisioning failed after sub-account creation",
                customer_id=str(customer.id),
                sub_account_id=sub_account_id,
            )
            return success_response(
                status.HTTP_201_CREATED,
                provisioned["error"],
                data=await build_customer_response(customer),
            )

        return success_response(
            status.HTTP_201_CREATED,
            "Customer and dedicated account created",
            data=await build_customer_response(customer),
        )

    async def link_nomba_sub_account(
        self,
        customer_id: str,
        body: LinkNombaSubAccountRequestSchema,
        merchant_id: UUID,
    ) -> dict[str, Any]:
        customer = await self._resolve_customer(customer_id, merchant_id)
        if not customer:
            return error_response(status.HTTP_404_NOT_FOUND, "Customer not found")

        if customer.status == CustomerStatus.ACTIVE:
            existing = await DedicatedAccount.filter(customer_id=customer.id).first()
            if existing:
                return error_response(
                    status.HTTP_409_CONFLICT,
                    "Customer is already provisioned with a dedicated account",
                )

        details = await NombaSubAccountService.fetch_details(
            account_id=body.nomba_sub_account_id,
        )
        if not details["success"]:
            status_code = details.get("status_code", status.HTTP_502_BAD_GATEWAY)
            http_status = (
                status.HTTP_404_NOT_FOUND
                if status_code == 404
                else status.HTTP_502_BAD_GATEWAY
            )
            return error_response(
                http_status,
                "Nomba sub-account not found or inaccessible",
                [str(details.get("message", "Unknown Nomba error"))],
            )

        sub_data = details["data"] or {}
        customer.nomba_sub_account_id = sub_data.get("account_id") or body.nomba_sub_account_id
        if sub_data.get("account_ref"):
            customer.nomba_sub_account_ref = sub_data["account_ref"]
        await customer.save()

        provisioned = await self._provision_virtual_account(customer)
        if provisioned.get("error"):
            return error_response(
                status.HTTP_502_BAD_GATEWAY,
                provisioned["error"],
                [str(provisioned.get("detail", ""))],
            )

        return success_response(
            status.HTTP_200_OK,
            "Nomba sub-account linked and virtual account provisioned",
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

        account = await DedicatedAccount.filter(customer_id=customer.id).first()
        if account and (body.name is not None or body.target_amount is not None):
            if body.name is not None:
                account.account_name = body.name
            await account.save()
            await NombaVirtualAccountService.update(
                account.account_ref,
                account_name=body.name,
                expected_amount=body.target_amount,
            )

        return success_response(
            status.HTTP_200_OK,
            "Customer updated",
            data=await build_customer_response(customer),
        )

    async def _provision_virtual_account(
        self,
        customer: Customer,
        body: CreateCustomerRequestSchema | None = None,
    ) -> dict[str, Any]:
        if not customer.nomba_sub_account_id:
            return {"error": "Customer has no Nomba sub-account ID"}

        existing = await DedicatedAccount.filter(customer_id=customer.id).first()
        if existing:
            customer.status = CustomerStatus.ACTIVE
            await customer.save()
            return {}

        account_ref = build_nomba_account_ref(customer.nomba_sub_account_ref)
        account_name = body.name if body else customer.name
        bvn = body.bvn if body else None
        expected_amount = body.target_amount if body else customer.target_amount

        nomba_result = await NombaVirtualAccountService.create(
            account_ref=account_ref,
            account_name=account_name,
            sub_account_id=customer.nomba_sub_account_id,
            bvn=bvn,
            expected_amount=expected_amount,
        )
        if not nomba_result["success"]:
            return {
                "error": "Failed to provision Nomba virtual account",
                "detail": nomba_result.get("message", "Unknown Nomba error"),
            }

        va_data = nomba_result["data"] or {}
        account_number = va_data.get("account_number")
        if not account_number:
            return {
                "error": "Nomba response missing bank account number",
                "detail": "Missing account_number in Nomba response",
            }

        await DedicatedAccount.create(
            id=uuid4(),
            customer=customer,
            nomba_va_id=va_data.get("nomba_va_id"),
            nomba_sub_account_id=customer.nomba_sub_account_id,
            account_number=account_number,
            account_name=account_name,
            account_ref=va_data.get("account_ref") or account_ref,
        )
        customer.status = CustomerStatus.ACTIVE
        await customer.save()

        account = await DedicatedAccount.filter(customer_id=customer.id).first()
        if account:
            from app.services.webhook_forwarder import WebhookForwarderService

            await WebhookForwarderService().emit_account_created(
                merchant_id=customer.merchant_id,
                customer=customer,
                account=account,
            )
        return {}

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
