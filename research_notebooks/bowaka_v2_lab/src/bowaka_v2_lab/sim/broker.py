"""Simulated broker — submit returns ``(status, parent_order_id, raw_response)``.

Per [Report §15.1 P0] remediation: on the submit-failure path, the simulator
emits a canonical ``broker_reject`` decision via
``schemas.decisions.build_broker_reject_record``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from .orders import ChildOrder, OrderPlan, OrderStatus, OrderSide, ParentOrder


@dataclass
class BrokerSubmitResult:
    status: OrderStatus
    parent_order_id: str
    raw_response: dict


class SimulatedBroker:
    """A deterministic broker stub.

    By default every submit succeeds. Tests may inject a
    ``fail_predicate(parent_order: ParentOrder) -> Optional[dict]`` that
    returns a dict (the raw reject response) to fail the submit, or None
    to accept.
    """

    def __init__(
        self,
        *,
        fail_predicate: Optional[Callable[[ParentOrder], Optional[dict]]] = None,
    ) -> None:
        self._fail = fail_predicate

    def submit(self, parent: ParentOrder) -> BrokerSubmitResult:
        if self._fail is not None:
            reject = self._fail(parent)
            if reject is not None:
                parent.status = OrderStatus.REJECTED
                parent.raw_broker_response = reject
                return BrokerSubmitResult(
                    status=OrderStatus.REJECTED,
                    parent_order_id=parent.parent_order_id,
                    raw_response=reject,
                )
        parent.status = OrderStatus.ACCEPTED
        accepted_response = {"status": "accepted", "broker": "sim"}
        parent.raw_broker_response = accepted_response
        return BrokerSubmitResult(
            status=OrderStatus.ACCEPTED,
            parent_order_id=parent.parent_order_id,
            raw_response=accepted_response,
        )
