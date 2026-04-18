"""Temporal workflow: triage activity + optional HITL signal + persist."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

from temporalio import workflow


@workflow.defn
class FraudTriageWorkflow:
    def __init__(self) -> None:
        self._approval: dict[str, Any] | None = None

    @workflow.signal
    def supervisor_decision(self, payload: dict[str, Any]) -> None:
        self._approval = payload

    @workflow.run
    async def run(self, inp: dict[str, Any]) -> dict[str, Any]:
        retry = workflow.RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=5,
        )
        result = await workflow.execute_activity(
            "run_triage_activity",
            inp,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry,
        )
        if not result.get("needs_hitl"):
            return result

        timeout_sec = int(inp.get("hitl_timeout_seconds", 120))
        try:
            await workflow.wait_condition(
                lambda: self._approval is not None,
                timeout=timedelta(seconds=timeout_sec),
            )
        except asyncio.TimeoutError:
            await workflow.execute_activity(
                "persist_hitl_activity",
                {
                    "case_id": inp["case_id"],
                    "resolution": {"status": "timeout", "note": "no_supervisor_signal"},
                },
                start_to_close_timeout=timedelta(seconds=60),
            )
            return {**result, "hitl_resolution": {"status": "timeout"}}

        if self._approval:
            await workflow.execute_activity(
                "persist_hitl_activity",
                {"case_id": inp["case_id"], "resolution": self._approval},
                start_to_close_timeout=timedelta(seconds=60),
            )
            return {**result, "hitl_resolution": self._approval}
        return result
