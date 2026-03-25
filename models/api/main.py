from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from models.schemas import EngagementRequest, ReimbursementPathwayReport, AgentState
from agents.orchestrator import build_graph
import logging, uuid

app = FastAPI(
    title="Women's Health Reimbursement Intelligence API",
    description="Investor-grade reimbursement pathway reports for women's healthtech companies.",
    version="1.0.0",
)

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
graph = build_graph()


@app.post("/engagements", response_model=dict, status_code=202)
async def create_engagement(
    request: EngagementRequest,
    token: str = Depends(oauth2_scheme),
):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = AgentState(request=request)

    try:
        result = await graph.ainvoke(initial_state, config=config)
        return {
            "thread_id": thread_id,
            "status": "complete" if not result.requires_human_review else "pending_review",
            "report_available": result.report is not None,
        }
    except Exception as e:
        logger.error(f"Engagement error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/engagements/{thread_id}/report", response_model=ReimbursementPathwayReport)
async def get_report(thread_id: str, token: str = Depends(oauth2_scheme)):
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    if not state or not state.values.get("report"):
        raise HTTPException(status_code=404, detail="Report not found or not yet generated")
    return state.values["report"]


@app.post("/engagements/{thread_id}/approve")
async def approve_human_review(thread_id: str, token: str = Depends(oauth2_scheme)):
    """Resume graph after analyst approval of speculative-risk engagements."""
    config = {"configurable": {"thread_id": thread_id}}
    await graph.aupdate_state(config, {"requires_human_review": False})
    result = await graph.ainvoke(None, config=config)
    return {"status": "resumed", "report_available": result.report is not None}


@app.get("/health")
async def health():
    return {"status": "ok"}
