import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from models.schemas import AgentState, CPTCodeEntry
from prompts.cpt_landscape import CPT_LANDSCAPE_SYSTEM, CPT_LANDSCAPE_HUMAN
import json, os

logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL_SYNTHESIS", "gpt-4o"),
    temperature=0,
)


def cpt_landscape_node(state: AgentState) -> AgentState:
    prompt = ChatPromptTemplate.from_messages([
        ("system", CPT_LANDSCAPE_SYSTEM),
        ("human", CPT_LANDSCAPE_HUMAN),
    ])

    chain = prompt | llm

    response = chain.invoke({
        "service_lines": [s.value for s in state.request.service_lines],
        "service_description": state.request.service_description or "",
        "target_cpt_codes": state.request.target_cpt_codes or [],
        "geography": state.request.geography,
    })

    try:
        raw = json.loads(response.content)
        state.cpt_landscape = [CPTCodeEntry(**entry) for entry in raw["cpt_codes"]]
        logger.info(f"CPT landscape: {len(state.cpt_landscape)} codes identified")
    except Exception as e:
        state.errors.append(f"cpt_landscape_node: {str(e)}")
        logger.error(f"CPT landscape parse error: {e}")

    return state
