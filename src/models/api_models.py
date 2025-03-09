from typing import List
from dataclasses import dataclass

from decimal import Decimal

from .shipment import Shipment


@dataclass
class GroupedShipments:
    shipments: List[Shipment]
    product: str
    origin: str
    destination: str

    subtotal_origin_weight: Decimal
    subtotal_destination_weight: Decimal
    subtotal_difference: Decimal
    subtotal_money: Decimal

    def __init__(self, product_name: str, origin: str, destination: str):
        self.shipments = []
        self.subtotal_origin_weight = Decimal("0")
        self.subtotal_destination_weight = Decimal("0")
        self.subtotal_difference = Decimal("0")
        self.subtotal_money = Decimal("0")
        self.product = product_name
        self.origin = origin
        self.destination = destination

    def add_shipment(self, shipment: Shipment) -> None:
        self.shipments.append(shipment)

    def update_subtotals(
        self,
        origin_weight: Decimal,
        destination_weight: Decimal,
        difference: Decimal,
        money: Decimal,
    ) -> None:
        self.subtotal_origin_weight += origin_weight
        self.subtotal_destination_weight += destination_weight
        self.subtotal_difference += difference
        self.subtotal_money += money
