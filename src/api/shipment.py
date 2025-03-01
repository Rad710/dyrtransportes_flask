from flask import request
from flask import jsonify
from flask import Response
from flask import make_response

from typing import Sequence
from typing import Tuple
from typing import Optional
from typing import List
from typing import Dict

from sqlalchemy import select
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from app_config import logger
from app_config import app
from app_config import db_session
from app_config import RequestWithUser

from decorators.token_required import token_required

from models.shipment import Shipment
from models.driver_payroll import DriverPayroll

from decimal import localcontext, ROUND_HALF_UP

from dataclasses import asdict

request: RequestWithUser


@app.route("/api/shipment/<int:shipment_code>", methods=["GET"])
@token_required
def get_shipment(shipment_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(Shipment).where(
            Shipment.shipment_code == shipment_code,
            Shipment.deleted == False,
            Shipment.modification_user == request.current_user.user_id,
        )

        shipment: Optional[Shipment] = db_session.scalar(stmt)
        if shipment is None:
            logger.error("fetch table Shipment, not found")
            return jsonify({"message": "No se encontró la Carga"}), 404

        logger.info("fetch table Shipment, found: %s", shipment.shipment_code)
        logger.debug("fetch table Shipment, found: %s", shipment)

        return jsonify(shipment), 200

    except SQLAlchemyError as e:
        logger.error("fetch table Shipment, error: %s", e)
        return jsonify({"message": "Error de transacción"}), 500


@app.route("/api/shipments", methods=["GET"])
@token_required
def get_shipment_list() -> Tuple[Response, int]:
    shipment_payroll_code_param: str | None = request.args.get("shipment_payroll_code")
    try:
        shipment_payroll_code: Optional[int] = (
            int(shipment_payroll_code_param) if shipment_payroll_code_param else None
        )
    except ValueError as e:
        logger.error("Invalid 'shipment_payroll_code' parameter %s", e)
        return jsonify({"message": "Parámetros inválidos"}), 400

    try:
        stmt = select(Shipment).where(
            Shipment.deleted == False,
            Shipment.modification_user == request.current_user.user_id,
        )

        if shipment_payroll_code:
            stmt = stmt.where(Shipment.shipment_payroll_code == shipment_payroll_code)

        shipments: Sequence[Shipment] = db_session.scalars(stmt).all()
        logger.info("fetch shipments table Shipment, len: %s", len(shipments))
        logger.debug("fetch shipments table Shipment, shipments: %s", shipments)
        return jsonify(shipments), 200

    except SQLAlchemyError as e:
        logger.error("fetch shipments table Shipment, error: %s", e)
        return jsonify({"message": "Error al obtener planillas"}), 500


@app.route("/api/shipments-aggregated", methods=["GET"])
@token_required
def get_aggregated_shipment_list() -> Tuple[Response, int]:
    shipment_payroll_code_param: str | None = request.args.get("shipment_payroll_code")
    if shipment_payroll_code_param is None:
        logger.error("Invalid 'shipment_payroll_code' parameter")
        return jsonify({"message": "Parámetros inválidos"}), 400

    try:
        shipment_payroll_code: int = int(shipment_payroll_code_param)
    except ValueError as e:
        logger.error("Invalid 'shipment_payroll_code' parameter %s", e)
        return jsonify({"message": "Parámetros inválidos"}), 400

    try:
        stmt = select(Shipment).where(
            Shipment.deleted == False,
            Shipment.modification_user == request.current_user.user_id,
            Shipment.shipment_payroll_code == shipment_payroll_code,
        )

        shipments: Sequence[Shipment] = db_session.scalars(stmt).all()

        aggregated_shipments: Dict[str, Dict] = {}
        # TODO: do this with a single query
        for shipment in shipments:
            shipment_product_route = (
                f"{shipment.product_name}|{shipment.origin}|{shipment.destination}"
            )

            if shipment_product_route not in aggregated_shipments:
                aggregated_shipments[shipment_product_route] = {
                    "shipments": [],
                    "subtotalOrigin": 0,
                    "subtotalDestination": 0,
                    "subtotalDifference": 0,
                    "subtotalMoney": 0,
                    "product": shipment.product_name,
                    "origin": shipment.origin,
                    "destination": shipment.destination,
                }

            aggregated_shipments[shipment_product_route]["shipments"].append(shipment)

            aggregated_shipments[shipment_product_route][
                "subtotalOrigin"
            ] += shipment.origin_weight
            aggregated_shipments[shipment_product_route][
                "subtotalDestination"
            ] += shipment.destination_weight
            aggregated_shipments[shipment_product_route]["subtotalDifference"] += (
                shipment.destination_weight - shipment.origin_weight
            )

            aggregated_shipments[shipment_product_route]["subtotalMoney"] += (
                shipment.price * shipment.destination_weight
            )

        result = list(aggregated_shipments.items())
        result.sort(key=lambda x: x[0].split("|"))
        result = [pair[1] for pair in result]

        logger.info(
            "fetch shipments table Shipment and aggregated, len: %s", len(shipments)
        )
        logger.debug(
            "fetch shipments table Shipment and aggregated, response: %s", shipments
        )
        return jsonify(result), 200

    except SQLAlchemyError as e:
        logger.error("fetch shipments table Shipment and aggregated, error: %s", e)
        return jsonify({"message": "Error al obtener planillas"}), 500


@app.route("/api/shipment", methods=["POST"])
@token_required
def post_shipment() -> Tuple[Response, int]:
    try:
        shipment_dict = request.get_json()
        driver_code: int | None = shipment_dict["driver_code"]

        driver_payroll_stmt = (
            select(DriverPayroll.payroll_code)
            .where(
                DriverPayroll.driver_code == driver_code,
                DriverPayroll.deleted == False,
                DriverPayroll.paid == False,
                DriverPayroll.modification_user == request.current_user.user_id,
            )
            .order_by(desc(DriverPayroll.payroll_code))
        )
        driver_payroll_code = db_session.scalar(driver_payroll_stmt)
        shipment_dict["driver_payroll_code"] = driver_payroll_code

        # json to db object
        payload = Shipment(
            **shipment_dict,
            modification_user=request.current_user.user_id,
        )

        # add to database
        logger.debug("insert table Shipment, payload: %s", payload)
        db_session.add(payload)

        db_session.commit()
        logger.info("inserted table Shipment, shipment: %s", payload.shipment_code)
        return (
            jsonify({**asdict(payload), "message": "Carga agregada exitosamente"}),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("insert table Shipment, invalid shipment error: %s", e)
        return jsonify({"message": f"Error, datos de la Carga inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("insert table Shipment, connection error: %s", e)

        return jsonify({"message": "Error al agregar Carga: problema de conexión"}), 503

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("insert table Shipment, error: %s", e)
        return jsonify({"message": "Error al agregar Carga"}), 500


@app.route("/api/shipment/<int:shipment_code>", methods=["PUT"])
@token_required
def put_shipment(shipment_code: int) -> Tuple[Response, int]:
    try:
        # get entry to update
        stmt = select(Shipment).where(
            Shipment.shipment_code == shipment_code,
            Shipment.modification_user == request.current_user.user_id,
        )
        entry_to_update: Optional[Shipment] = db_session.scalar(stmt)

        if entry_to_update is None:
            logger.error("update table Shipment, shipment not found")
            return jsonify({"message": "Carga no encontrada"}), 404

        # json to db object
        payload = Shipment(
            **request.get_json(), modification_user=request.current_user.user_id
        )

        entry_to_update.shipment_date = payload.shipment_date

        entry_to_update.driver_name = payload.driver_name
        entry_to_update.truck_plate = payload.truck_plate
        entry_to_update.trailer_plate = payload.trailer_plate
        entry_to_update.driver_code = payload.driver_code

        entry_to_update.product_code = payload.product_code
        entry_to_update.product_name = payload.product_name

        entry_to_update.route_code = payload.route_code
        entry_to_update.origin = payload.origin
        entry_to_update.destination = payload.destination
        entry_to_update.price = payload.price
        entry_to_update.payroll_price = payload.payroll_price

        entry_to_update.dispatch_code = payload.dispatch_code
        entry_to_update.receipt_code = payload.receipt_code
        entry_to_update.origin_weight = payload.origin_weight
        entry_to_update.destination_weight = payload.destination_weight
        entry_to_update.shipment_payroll_code = payload.shipment_payroll_code
        entry_to_update.driver_payroll_code = payload.driver_payroll_code
        entry_to_update.deleted = payload.deleted
        entry_to_update.modification_user = payload.modification_user

        logger.info("update table Shipment, payload: %s", entry_to_update)

        db_session.commit()
        logger.info("updated table Shipment, shipment: %s", shipment_code)
        return (
            jsonify(
                {**asdict(entry_to_update), "message": "Carga actualizada exitosamente"}
            ),
            200,
        )

    except (TypeError, ValueError, KeyError) as e:
        logger.error("update table Shipment, invalid shipment error: %s", e)
        return jsonify({"message": f"Error, datos de la Carga inválidos ({e})"}), 500

    except OperationalError as e:
        db_session.rollback()
        logger.error("update table Shipment, connection error: %s", e)

        return (
            jsonify({"message": "Error al actualizar Carga: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("update table Shipment, error: %s", e)
        return jsonify({"message": "Error al actualizar Carga"}), 500


@app.route("/api/shipment/<int:shipment_code>", methods=["DELETE"])
@token_required
def delete_shipment(shipment_code: int) -> Tuple[Response, int]:
    try:
        stmt = select(Shipment).where(
            Shipment.shipment_code == shipment_code,
            Shipment.modification_user == request.current_user.user_id,
        )
        existing_entry: Optional[Shipment] = db_session.scalar(stmt)

        if existing_entry is None:
            logger.error("delete table Shipment, shipment not found")
            return jsonify({"message": "Carga no encontrada"}), 404

        existing_entry.deleted = True
        existing_entry.modification_user = request.current_user.user_id
        db_session.commit()
        logger.info("delete table Shipment, shipment: %s", shipment_code)
        return jsonify({"message": "Carga eliminada exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table Shipment, connection error: %s", e)
        return (
            jsonify({"message": "Error al eliminar Carga: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table Shipment, error: %s", e)
        return jsonify({"message": "Error al eliminar Carga"}), 500


@app.route("/api/shipments", methods=["DELETE"])
@token_required
def delete_shipment_list() -> Tuple[Response, int]:
    if (request.data is None) or (not request.is_json):
        logger.error("delete shipments table Shipment, shipment list is empty")
        return jsonify({"message": "Error al eliminar Carga: Carga no encontrada"}), 404

    shipment_list: List[int] = request.get_json()
    logger.debug("delete shipments table Shipment, payload: %s", shipment_list)

    try:
        for shipment_code in shipment_list:
            stmt = select(Shipment).where(
                Shipment.shipment_code == shipment_code,
                Shipment.modification_user == request.current_user.user_id,
            )
            shipment: Optional[Shipment] = db_session.scalar(stmt)

            if shipment is None:
                return (
                    jsonify(
                        {"message": "Error al eliminar Carga: Carga no encontrada"}
                    ),
                    404,
                )

            shipment.deleted = True
            shipment.modification_user = request.current_user.user_id
            logger.info("delete table Shipment, shipment: %s", shipment_code)

        db_session.commit()
        return jsonify({"message": "Carga eliminada exitosamente"}), 200

    except OperationalError as e:
        db_session.rollback()
        logger.error("delete table Shipment, connection error: %s", e)
        return (
            jsonify({"message": "Error al eliminar Carga: problema de conexión"}),
            503,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error("delete table Shipment, error: %s", e)
        return jsonify({"message": "Error al eliminar Carga"}), 500


@app.route("/api/export-shipments", methods=["GET"])
@token_required
def export_shipments() -> Tuple[Response, int]:
    # Similar implementation to export_routes, but for shipments
    # This is an additional endpoint that matches the style of the route API
    # Add implementation as needed

    # Example implementation skeleton:
    shipment_response, code = get_shipment_list()

    if code != 200 or not shipment_response.is_json or shipment_response.json is None:
        logger.error("export Shipments, fetch Shipments error")
        return jsonify({"message": "Error enviar archivo Excel"}), 500

    # Implementation would continue here with Excel generation
    # Similar to the implementation in export_routes

    return jsonify({"message": "Not implemented yet"}), 501
