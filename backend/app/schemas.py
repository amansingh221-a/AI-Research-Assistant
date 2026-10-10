from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DocumentMetadata(BaseModel):
    id: str
    filename: str
    file_size: int
    page_count: int
    is_scanned: bool
    processing_status: str
    error_message: Optional[str] = None
    created_at: str

class SummaryRequest(BaseModel):
    length_type: str = Field(default="standard", description="short, standard, or detailed")

class StructuredSummary(BaseModel):
    paper_title: str = "Not found in document"
    authors: str = "Not found in document"
    publication_year: str = "Not found in document"
    research_topic: str = "Not found in document"
    main_research_question: str = "Not found in document"
    research_objective: str = "Not found in document"
    problem_addressed: str = "Not found in document"
    methodology: str = "Not found in document"
    dataset_or_sample: str = "Not found in document"
    important_findings: List[str] = []
    results_and_measurements: str = "Not found in document"
    authors_conclusions: str = "Not found in document"
    limitations: List[str] = []
    future_work: List[str] = []
    important_terminology: Dict[str, str] = {}
    simple_explanation: str = "Not found in document"
    executive_summary: str = "Not found in document"

class Citation(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    excerpt: str

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    is_grounded: bool

class ComparisonRequest(BaseModel):
    document_ids: List[str]

class ResearchGapRequest(BaseModel):
    document_ids: List[str]

class ReportRequest(BaseModel):
    title: str
    document_ids: List[str]
    report_type: str = "consolidated"