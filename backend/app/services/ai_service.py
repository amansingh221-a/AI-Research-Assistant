import os
import json
import httpx
from typing import Dict, Any, List, Optional
from app.schemas import StructuredSummary, Citation, ChatResponse

class AIService:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.api_key = os.getenv("AI_API_KEY", "").strip()
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")
        self.base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")

    def is_configured(self) -> bool:
        if self.provider == "mock":
            return True
        return bool(self.api_key)

    async def _call_llm(self, prompt: str, system_prompt: str = "You are an expert AI Research Assistant.") -> str:
        if not self.is_configured():
            raise ValueError("AI Provider API key is missing. Please configure AI_API_KEY in environment settings.")

        if self.provider == "mock":
            return json.dumps({
                "paper_title": "Sample Paper Title",
                "authors": "Jane Doe, John Smith",
                "publication_year": "2024",
                "executive_summary": "This mock summary represents a successfully extracted paper.",
                "important_findings": ["Finding 1: High accuracy achieved", "Finding 2: Scalability verified"],
                "limitations": ["Limited dataset size"],
                "future_work": ["Evaluate on larger benchmarks"]
            })

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            if res.status_code != 200:
                raise RuntimeError(f"AI Provider error ({res.status_code}): {res.text}")
            data = res.json()
            return data["choices"][0]["message"]["content"]

    async def generate_summary(self, chunks_text: str, length_type: str = "standard") -> Dict[str, Any]:
        system_instruction = (
            "You are ResearchMate AI. Extract structured summary details ONLY from the provided text. "
            "If a field is not found, set its value to 'Not found in document'. Never invent findings or metrics."
        )
        prompt = f"""
Analyze the following paper excerpt and generate a JSON summary matching this schema:
{{
  "paper_title": "...",
  "authors": "...",
  "publication_year": "...",
  "research_topic": "...",
  "main_research_question": "...",
  "research_objective": "...",
  "problem_addressed": "...",
  "methodology": "...",
  "dataset_or_sample": "...",
  "important_findings": ["..."],
  "results_and_measurements": "...",
  "authors_conclusions": "...",
  "limitations": ["..."],
  "future_work": ["..."],
  "important_terminology": {{"term": "definition"}},
  "simple_explanation": "...",
  "executive_summary": "..."
}}

Summary Detail Level: {length_type.upper()}

DOCUMENT TEXT:
{chunks_text[:12000]}
"""
        response_raw = await self._call_llm(prompt, system_instruction)
        try:
            cleaned = response_raw.strip().strip("```json").strip("```").strip()
            data = json.loads(cleaned)
            return data
        except Exception:
            return StructuredSummary(executive_summary=response_raw[:500]).model_dump()

    async def answer_question(self, question: str, retrieved_chunks: List[Dict[str, Any]], filename: str, doc_id: str) -> ChatResponse:
        context_str = "\n\n".join([
            f"[Page {c['page_number']}]\n{c['content']}" for c in retrieved_chunks
        ])

        system_prompt = (
            "You are ResearchMate AI. Answer questions using ONLY the retrieved context below. "
            "If the context does not contain enough information, explicitly state: 'The document does not provide sufficient evidence to answer this question.' "
            "Do not invent facts or page numbers."
        )

        prompt = f"Question: {question}\n\nRetrieved Document Context:\n{context_str}"
        answer_text = await self._call_llm(prompt, system_prompt)

        citations = [
            Citation(
                document_id=doc_id,
                document_name=filename,
                page_number=c["page_number"],
                excerpt=c["content"][:200] + "..."
            )
            for c in retrieved_chunks[:3]
        ]

        is_grounded = "does not provide sufficient evidence" not in answer_text.lower()
        return ChatResponse(answer=answer_text, citations=citations, is_grounded=is_grounded)

    async def compare_papers(self, papers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = f"""
Compare the following research papers based ONLY on their extracted evidence.

Papers:
{json.dumps(papers_data, indent=2)}

Provide output as JSON with keys:
1. matrix: List of comparative dicts covering [Title, Year, Methodology, Dataset, Core Findings, Limitations]
2. narrative_analysis: Comprehensive text comparison.
3. key_takeaways: Concise summary of similarities, differences, and conflicting results.
"""
        response_raw = await self._call_llm(prompt)
        try:
            cleaned = response_raw.strip().strip("```json").strip("```").strip()
            return json.loads(cleaned)
        except Exception:
            return {"narrative_analysis": response_raw, "matrix": [], "key_takeaways": "Comparison completed."}

    async def analyze_gaps(self, papers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = f"""
Identify research gaps, unaddressed limitations, and future questions from these papers:
{json.dumps(papers_data, indent=2)}

Output JSON format:
{{
  "research_gaps": [
    {{
      "gap_title": "...",
      "description": "...",
      "source_paper": "...",
      "confidence_level": "High/Medium/Low",
      "supporting_evidence": "...",
      "validation_needed": "..."
    }}
  ],
  "disclaimer": "Analysis is strictly limited to the provided documents."
}}
"""
        response_raw = await self._call_llm(prompt)
        try:
            cleaned = response_raw.strip().strip("```json").strip("```").strip()
            return json.loads(cleaned)
        except Exception:
            return {"research_gaps": [], "disclaimer": "Analysis limited to uploaded files."}