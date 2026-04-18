"""Temporal worker process."""

from __future__ import annotations

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from fraud_agent_orchestrator.activities.hitl import persist_hitl_activity
from fraud_agent_orchestrator.activities.triage import run_triage_activity
from fraud_agent_orchestrator.settings.env import get_settings
from fraud_agent_orchestrator.temporal_layer.workflow import FraudTriageWorkflow

logger = logging.getLogger(__name__)


async def _run() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    client = await Client.connect(
        settings.temporal_target,
        namespace=settings.temporal_namespace,
    )
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[FraudTriageWorkflow],
        activities=[run_triage_activity, persist_hitl_activity],
    )
    logger.info(
        "Temporal worker up: queue=%s target=%s",
        settings.temporal_task_queue,
        settings.temporal_target,
    )
    await worker.run()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
