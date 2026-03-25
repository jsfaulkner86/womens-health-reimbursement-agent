import pytest
from unittest.mock import patch, MagicMock
from models.schemas import (
    AgentState, EngagementRequest, EngagementMode,
    ServiceLine, CPTCodeEntry, CoverageStatus,
)


@pytest.fixture
def feasibility_request():
    return EngagementRequest(
        company_name="Acme Women's Health",
        service_lines=[ServiceLine.MENOPAUSE, ServiceLine.PCOS],
        target_payers=["Aetna", "BCBS"],
        geography=["CA", "TX"],
        engagement_mode=EngagementMode.FEASIBILITY,
        service_description="Continuous hormonal monitoring platform with AI-guided dosage recommendations",
        target_cpt_codes=["99213", "96160"],
    )


@pytest.fixture
def mock_cpt_landscape():
    return [
        CPTCodeEntry(
            code="99213",
            descriptor="Office visit, established patient, low complexity",
            coverage_status=CoverageStatus.COVERED,
            rvu=1.3,
            medicare_allowed_amount=76.34,
        ),
        CPTCodeEntry(
            code="96160",
            descriptor="Health risk assessment, patient-focused",
            coverage_status=CoverageStatus.COVERED_WITH_RESTRICTIONS,
            payer_notes="Requires diagnosis of hormonal imbalance",
        ),
    ]


def test_engagement_request_validation(feasibility_request):
    assert feasibility_request.engagement_mode == EngagementMode.FEASIBILITY
    assert ServiceLine.MENOPAUSE in feasibility_request.service_lines


def test_agent_state_initialization(feasibility_request):
    state = AgentState(request=feasibility_request)
    assert state.cpt_landscape == []
    assert state.requires_human_review is False
    assert state.errors == []


@patch("agents.cpt_landscape.ChatOpenAI")
def test_cpt_landscape_node_parses_response(mock_llm, feasibility_request, mock_cpt_landscape):
    import json
    from agents.cpt_landscape import cpt_landscape_node

    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "cpt_codes": [c.model_dump() for c in mock_cpt_landscape]
    })
    mock_llm.return_value.invoke.return_value = mock_response

    state = AgentState(request=feasibility_request)
    result = cpt_landscape_node(state)
    assert len(result.cpt_landscape) == 2
    assert result.cpt_landscape.code == "99213"


def test_gap_classifier_speculative_sets_human_review(feasibility_request):
    from agents.gap_classifier import gap_classifier_node
    import json
    from unittest.mock import patch

    mock_output = {
        "gap_analysis": {
            "uncompensated_service_volume_estimate": 5000,
            "avg_allowed_amount_per_encounter": 120.0,
            "estimated_annual_revenue_gap": 600000.0,
            "gap_narrative": "Significant uncompensated volume due to lack of CPT pathway.",
        },
        "investor_risk_rating": "speculative",
        "comparable_precedents": ["CGM coverage trajectory 2017-2021"],
        "payer_strategy_recommendations": ["Target Aetna Innovation team first"],
    }

    with patch("agents.gap_classifier.ChatOpenAI") as mock_llm:
        mock_resp = MagicMock()
        mock_resp.content = json.dumps(mock_output)
        mock_llm.return_value.invoke.return_value = mock_resp

        state = AgentState(request=feasibility_request)
        result = gap_classifier_node(state)
        assert result.requires_human_review is True
