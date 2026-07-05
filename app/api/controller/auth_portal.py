from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, File, Form, Response, UploadFile

from app.api.security.portal_auth import ValidPortalMerchant
from app.schemas.requests.auth import (
    ChangePasswordRequestSchema,
    LoginAuthRequestSchema,
    RegisterAuthRequestSchema,
)
from app.schemas.requests.onboarding import (
    OnboardingAddressRequestSchema,
    OnboardingBusinessRequestSchema,
    OnboardingVerificationRequestSchema,
)
from app.schemas.requests.settings import (
    UpdateProfileSettingsRequestSchema,
    UpdateWebhookSettingsRequestSchema,
)
from app.services.auth import AuthService, OnboardingService, SettingsService
from app.services.file_upload import FileUploadService
from app.settings import settings
from app.utils.session_tokens import create_session_token


def _set_session_cookie(response: Response, merchant_id: UUID) -> None:
    token = create_session_token(merchant_id)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.PROD_ENV,
        max_age=settings.SESSION_JWT_EXPIRY_HOURS * 3600,
    )


async def register_auth(
    body: RegisterAuthRequestSchema,
    response: Response,
    service: Annotated[AuthService, Depends()],
) -> dict[str, Any]:
    result = await service.register(body)
    merchant_id = result["data"]["merchant"]["id"]
    _set_session_cookie(response, merchant_id)
    return result


async def login_auth(
    body: LoginAuthRequestSchema,
    response: Response,
    service: Annotated[AuthService, Depends()],
) -> dict[str, Any]:
    result = await service.login(body)
    merchant_id = result["data"]["merchant"]["id"]
    _set_session_cookie(response, merchant_id)
    return result


async def logout_auth(response: Response) -> dict[str, Any]:
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return {
        "status": "success",
        "status_code": 200,
        "message": "Logged out",
        "data": None,
    }


async def auth_me(
    merchant: ValidPortalMerchant,
    service: Annotated[AuthService, Depends()],
) -> dict[str, Any]:
    return await service.me(merchant)


async def onboarding_business(
    body: OnboardingBusinessRequestSchema,
    merchant: ValidPortalMerchant,
    service: Annotated[OnboardingService, Depends()],
) -> dict[str, Any]:
    return await service.update_business(merchant, body)


async def onboarding_address(
    body: OnboardingAddressRequestSchema,
    merchant: ValidPortalMerchant,
    service: Annotated[OnboardingService, Depends()],
) -> dict[str, Any]:
    return await service.update_address(merchant, body)


async def onboarding_verification(
    body: OnboardingVerificationRequestSchema,
    merchant: ValidPortalMerchant,
    service: Annotated[OnboardingService, Depends()],
) -> dict[str, Any]:
    return await service.update_verification(merchant, body)


async def onboarding_document(
    merchant: ValidPortalMerchant,
    file: Annotated[
        UploadFile,
        File(description="KYB document (PDF, JPG, or PNG — max 10MB)"),
    ],
    document_type: Annotated[
        str,
        Form(
            description="Document category, e.g. cac_certificate or address_proof",
            max_length=50,
        ),
    ],
    upload_service: Annotated[FileUploadService, Depends()],
    service: Annotated[OnboardingService, Depends()],
) -> dict[str, Any]:
    folder = f"uploads/kyb/{merchant}"
    upload_result = await upload_service.upload_single_file(file, folder=folder)
    return await service.save_document(merchant, document_type, upload_result["data"])


async def onboarding_submit(
    merchant: ValidPortalMerchant,
    service: Annotated[OnboardingService, Depends()],
) -> dict[str, Any]:
    return await service.submit(merchant)


async def onboarding_status(
    merchant: ValidPortalMerchant,
    service: Annotated[OnboardingService, Depends()],
) -> dict[str, Any]:
    return await service.status(merchant)


async def settings_credentials(
    merchant: ValidPortalMerchant,
    service: Annotated[SettingsService, Depends()],
) -> dict[str, Any]:
    return await service.get_credentials(merchant)


async def settings_rotate_credentials(
    merchant: ValidPortalMerchant,
    service: Annotated[SettingsService, Depends()],
) -> dict[str, Any]:
    return await service.rotate_credentials(merchant)


async def settings_get_webhook(
    merchant: ValidPortalMerchant,
    service: Annotated[SettingsService, Depends()],
) -> dict[str, Any]:
    return await service.get_webhook(merchant)


async def settings_update_webhook(
    body: UpdateWebhookSettingsRequestSchema,
    merchant: ValidPortalMerchant,
    service: Annotated[SettingsService, Depends()],
) -> dict[str, Any]:
    return await service.update_webhook(merchant, body)


async def settings_test_webhook(
    merchant: ValidPortalMerchant,
    service: Annotated[SettingsService, Depends()],
) -> dict[str, Any]:
    return await service.test_webhook(merchant)


async def settings_get_profile(
    merchant: ValidPortalMerchant,
    service: Annotated[SettingsService, Depends()],
) -> dict[str, Any]:
    return await service.get_profile(merchant)


async def settings_update_profile(
    body: UpdateProfileSettingsRequestSchema,
    merchant: ValidPortalMerchant,
    service: Annotated[SettingsService, Depends()],
) -> dict[str, Any]:
    return await service.update_profile(merchant, body)


async def settings_change_password(
    body: ChangePasswordRequestSchema,
    merchant: ValidPortalMerchant,
    service: Annotated[SettingsService, Depends()],
) -> dict[str, Any]:
    return await service.change_password(merchant, body)
