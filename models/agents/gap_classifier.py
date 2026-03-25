import logging, os, json
from langchain_openai import ChatOpenAI
from models.schemas import AgentState, GapAnalysis, InvestorRiskRating, CoverageStatus
from prompts.gap_classifier import GAP_CLASSIFIER_SYSTEM

logger = logging.getLogger(__name__)
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL_REASONING", "o3"), temperature=1)

HIGH_RISK_THRESHOLD = 0.5


def gap_classifier_node(state: AgentState) -> AgentState:
    no_pathway_count = sum(
        1 for c in state.cpt_landscape
        if c.coverage_status in (CoverageStatus.NO_PATHWAY, CoverageStatus.UNLABELED_USE)
    )
    total = len(state.cpt_landscape) or 1
    gap_ratio = no_pathway_count / total

    context = json.dumps({
        "cpt_landscape": [c.model_dump() for c in state.cpt_landscape],
        "policy_findings": state.policy_findings,
        "gap_ratio": gap_ratio,
        "service_lines": [s.value for s in state.request.service_lines],
        "geography": state.request.geography,
    })

    response = llm.invoke([
        {"role": "system", "content": GAP_CLASSIFIER_SYSTEM},
        {"role": "user", "content": context},
    ])

    try:
        raw = json.loads(response.content)
        state.gap_analysis = GapAnalysis(**raw["gap_analysis"])
        state.policy_findings["_risk_rating"] = raw["investor_risk_rating"]
        state.policy_findings["_comparable_precedents"] = raw.get("comparable_precedents", [])
        state.policy_findings["_payer_strategy"] = raw.get("payer_strategy_recommendations", [])

        if raw["investor_risk_rating"] == InvestorRiskRating.SPECULATIVE:
            state.requires_human_review = True
            state.escalation_reason = "Speculative risk rating requires analyst review before delivery"

        logger.info(f"Risk rating: {raw['investor_risk_rating']} | Gap ratio: {gap_ratio:.2%}")
    except Exception as e:
        state.errors.append(f"gap_classifier_node: {str(e)}")
        logger.error(f"Gap classifier parse error: {e}")

    return state
