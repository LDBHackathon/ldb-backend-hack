import pytest

from app.integrations.nomba.helpers import (
    build_nomba_account_ref,
    normalize_nomba_account_name,
    parse_virtual_account_response,
)


def test_build_nomba_account_ref_generates_compliant_value() -> None:
    account_ref = build_nomba_account_ref()
    assert 16 <= len(account_ref) <= 64


def test_build_nomba_account_ref_accepts_valid_candidate() -> None:
    candidate = "1oWbJQQHLyQqqf1SwxjSpudeA21"
    assert build_nomba_account_ref(candidate) == candidate


def test_normalize_nomba_account_name_enforces_minimum_length() -> None:
    with pytest.raises(ValueError, match="at least 8 characters"):
        normalize_nomba_account_name("Ada")


def test_parse_virtual_account_response_maps_bank_fields() -> None:
    parsed = parse_virtual_account_response(
        {
            "accountRef": "1oWbJQQHLyQqqf1SwxjSpudeA21",
            "accountName": "Daniel Scorsese",
            "bankAccountNumber": "9391076543",
            "bankName": "Nombank MFB",
            "accountId": "nomba-account-id",
            "accountHolderId": "holder-id",
            "currency": "NGN",
        }
    )
    assert parsed["account_number"] == "9391076543"
    assert parsed["nomba_va_id"] == "nomba-account-id"
    assert parsed["account_ref"] == "1oWbJQQHLyQqqf1SwxjSpudeA21"
