"""The @validates rules of the models, checked without a database."""

from datetime import datetime
from decimal import Decimal

import pytest

from models.driver import Driver
from models.driver_payroll import DriverPayroll
from models.product import Product
from models.route import Route
from models.shipment import Shipment


@pytest.mark.parametrize(
    "field",
    ["driver_id", "driver_name", "driver_surname", "truck_plate", "trailer_plate"],
)
@pytest.mark.parametrize("value", ["", "   ", None, 123])
def test_driver_text_fields_reject_empty_values(field, value):
    with pytest.raises((ValueError, TypeError)):
        Driver(**{field: value})


def test_driver_accepts_valid_values():
    driver = Driver(
        driver_id="1234567",
        driver_name="JUAN",
        driver_surname="PEREZ",
        truck_plate="ABC123",
        trailer_plate="TRA123",
    )

    assert driver.driver_name == "JUAN"
    assert driver.truck_plate == "ABC123"


@pytest.mark.parametrize("value", ["", "   ", None])
def test_product_name_rejects_empty_values(value):
    with pytest.raises((ValueError, TypeError)):
        Product(product_name=value)


@pytest.mark.parametrize("field", ["origin", "destination"])
@pytest.mark.parametrize("value", ["", "  ", None])
def test_route_places_reject_empty_values(field, value):
    with pytest.raises((ValueError, TypeError)):
        Route(**{field: value})


@pytest.mark.parametrize("field", ["price", "payroll_price"])
def test_route_prices_accept_decimal_strings(field):
    route = Route(**{field: "120.75"})

    assert getattr(route, field) == Decimal("120.75")


@pytest.mark.parametrize("field", ["price", "payroll_price"])
def test_route_prices_reject_negative_values(field):
    with pytest.raises(ValueError, match="non-negative"):
        Route(**{field: "-1"})


@pytest.mark.parametrize("field", ["price", "payroll_price"])
@pytest.mark.parametrize("value", ["no-es-un-numero", ""])
def test_route_prices_reject_values_that_are_not_numbers(field, value):
    with pytest.raises(ValueError):
        Route(**{field: value})


@pytest.mark.parametrize("field", ["price", "payroll_price"])
def test_route_prices_reject_the_wrong_type(field):
    with pytest.raises(TypeError):
        Route(**{field: [1]})


def test_shipment_date_parses_the_http_date_format():
    shipment = Shipment(shipment_date="Sun, 01 Mar 2026 00:00:00 GMT")

    assert shipment.shipment_date == datetime(2026, 3, 1)


def test_shipment_date_accepts_a_datetime():
    moment = datetime(2026, 3, 1)

    assert Shipment(shipment_date=moment).shipment_date == moment


@pytest.mark.parametrize("value", ["2026-03-01", "01/03/2026", "", "mañana"])
def test_shipment_date_rejects_other_formats(value):
    with pytest.raises(ValueError, match="Invalid shipment_date"):
        Shipment(shipment_date=value)


@pytest.mark.parametrize("field", ["price", "payroll_price"])
def test_shipment_prices_reject_negative_values(field):
    with pytest.raises(ValueError, match="non-negative"):
        Shipment(**{field: "-0.01"})


def test_driver_payroll_timestamp_parses_the_http_date_format():
    payroll = DriverPayroll(payroll_timestamp="Tue, 31 Mar 2026 00:00:00 GMT")

    assert payroll.payroll_timestamp == datetime(2026, 3, 31)


def test_driver_payroll_timestamp_rejects_other_formats():
    with pytest.raises(ValueError):
        DriverPayroll(payroll_timestamp="2026-03-31")
