import logging, os, json
from datetime import datetime
from langchain_openai import ChatOpenAI
from models.schemas import (
    AgentState, ReimbursementPathwayReport, CoverageStatus,
    PathwayMilestone, InvestorRiskRating
)
from prompts.narrative_generator import NARRATIVE_SYSTEM
from reports.renderer import render_pdf

logger = logging.getLogger(__name__)
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL_SYNTHESIS", "gpt-4o"), temperature=0.3)


def narrative_generator_node(state: AgentState) -> AgentState:
    context = json.dumps({
        "company_name": state.request.company_name,
        "service_lines": [s.value for s in state.request.service_lines],
        "cpt_landscape": [c.model_dump() for c in state.cpt_landscape],
        "policy_findings": state.policy_findings,
        "gap_analysis": state.gap_analysis.model_dump() if state.gap_analysis else {},
        "geography": state.request.geography,
        "target_payers": state.request.target_payers,
    })

    response = llm.invoke([
        {"role": "system", "content": NARRATIVE_SYSTEM},
        {"role": "user", "content": context},
    ])

    try:
        raw = json.loads(response.content)
        milestones = [PathwayMilestone(**m) for m in raw["pathway_milestones"]]
        current_status = {
            k: CoverageStatus(v)
            for k, v in raw["current_reimbursement_status"].items()
        }

        state.report = ReimbursementPathwayReport(
            company_name=state.request.company_name,
            service_lines=state.request.service_lines,
            engagement_mode=state.request.engagement_mode,
            current_reimbursement_status=current_status,
            cpt_landscape=state.cpt_landscape,
            gap_quantification=state.gap_analysis,
            pathway_milestones=milestones,
            comparable_precedents=state.policy_findings.get("_comparable_precedents", []),
            payer_strategy_recommendations=state.policy_findings.get("_payer_strategy", []),
            investor_risk_rating=InvestorRiskRating(state.policy_findings.get("_risk_rating", "high")),
            investor_executive_summary=raw["investor_executive_summary"],
            investor_status_summary=raw["investor_status_summary"],
            investor_pathway_narrative=raw["investor_pathway_narrative"],
            data_sources=raw.get("data_sources", []),
            generated_at=datetime.utcnow(),
            confidence_score=raw.get("confidence_score", 0.75),
        )
        logger.info(f"Report generated for {state.request.company_name}")
        render_pdf(state.report)
    except Exception as e:
        state.errors.append(f"narrative_generator_node: {str(e)}")
        logger.error(f"Narrative generator error: {e}")

    return state
