from typing import List
from typing import Dict
from typing import Sequence
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


def shipment_list_to_grouped_shipments_list(
    shipments: Sequence[Shipment] | List[Shipment],
) -> List[GroupedShipments]:
    grouped_shipments_dict: Dict[str, GroupedShipments] = {}
    for shipment in shipments:
        shipment_route_product = f"R{shipment.route_code}|P{shipment.product_code}"

        if shipment_route_product not in grouped_shipments_dict:
            grouped_shipments_dict[shipment_route_product] = GroupedShipments(
                product_name=shipment.product_name,
                origin=shipment.origin,
                destination=shipment.destination,
            )

        grouped_shipments_dict[shipment_route_product].add_shipment(shipment)

        grouped_shipments_dict[shipment_route_product].update_subtotals(
            origin_weight=shipment.origin_weight,
            destination_weight=shipment.destination_weight,
            difference=shipment.destination_weight - shipment.origin_weight,
            money=shipment.price * shipment.destination_weight,
        )

    result = list(grouped_shipments_dict.items())
    result.sort(key=lambda x: x[0].split("|"))
    return [pair[1] for pair in result]
