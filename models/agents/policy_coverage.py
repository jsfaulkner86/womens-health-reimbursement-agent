import logging, os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from models.schemas import AgentState
from prompts.policy_coverage import POLICY_COVERAGE_SYSTEM

logger = logging.getLogger(__name__)

llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL_SYNTHESIS", "gpt-4o"), temperature=0)
embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"))


def _build_retriever(service_lines: list[str], payers: list[str]):
    client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    vectorstore = Qdrant(
        client=client,
        collection_name=os.getenv("QDRANT_COLLECTION", "womens_health_policy"),
        embeddings=embeddings,
    )
    filter_conditions = {"service_line": {"$in": service_lines}}
    return vectorstore.as_retriever(
        search_kwargs={"k": 12, "filter": filter_conditions}
    )


def policy_coverage_node(state: AgentState) -> AgentState:
    service_lines = [s.value for s in state.request.service_lines]
    retriever = _build_retriever(service_lines, state.request.target_payers)

    findings = {}
    for cpt_entry in state.cpt_landscape:
        query = (
            f"Coverage policy for CPT {cpt_entry.code} "
            f"({cpt_entry.descriptor}) in {', '.join(service_lines)}"
        )
        docs = retriever.get_relevant_documents(query)
        context = "\n\n".join([d.page_content for d in docs])

        response = llm.invoke([
            {"role": "system", "content": POLICY_COVERAGE_SYSTEM},
            {"role": "user", "content": (
                f"CPT: {cpt_entry.code} — {cpt_entry.descriptor}\n"
                f"Payers: {state.request.target_payers}\n"
                f"Geography: {state.request.geography}\n\n"
                f"Policy context:\n{context}"
            )},
        ])
        findings[cpt_entry.code] = response.content
        logger.info(f"Policy findings for {cpt_entry.code} retrieved")

    state.policy_findings = findings
    return state
