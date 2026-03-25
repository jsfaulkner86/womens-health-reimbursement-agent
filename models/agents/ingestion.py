"""
Performance mode: normalizes EDI 835/837, CSV, and PDF flat files
into structured ClaimsRecord objects for downstream benchmarking.
Phase 2 — stub included for interface completeness.
"""
import logging
from models.schemas import AgentState

logger = logging.getLogger(__name__)


def ingestion_node(state: AgentState) -> AgentState:
    # TODO Phase 2: implement EDI x12 835/837 parser + CSV normalizer
    logger.info("Ingestion node: Phase 2 — flat file normalization pending")
    state.policy_findings["_ingestion_status"] = "phase_2_pending"
    return state
