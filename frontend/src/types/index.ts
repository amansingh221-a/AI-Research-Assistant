export interface DocumentMetadata {
  id: string;
  filename: string;
  file_size: number;
  page_count: number;
  is_scanned: boolean;
  processing_status: 'processed' | 'scanned_pdf_warning' | 'failed';
  error_message?: string;
  created_at: string;
}

export interface StructuredSummary {
  paper_title: string;
  authors: string;
  publication_year: string;
  research_topic: string;
  main_research_question: string;
  research_objective: string;
  problem_addressed: string;
  methodology: string;
  dataset_or_sample: string;
  important_findings: string[];
  results_and_measurements: string;
  authors_conclusions: string;
  limitations: string[];
  future_work: string[];
  important_terminology: Record<string, string>;
  simple_explanation: string;
  executive_summary: string;
}

export interface Citation {
  document_id: string;
  document_name: string;
  page_number: number;
  excerpt: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  is_grounded?: boolean;
}

export interface ResearchGap {
  gap_title: string;
  description: string;
  source_paper: string;
  confidence_level: 'High' | 'Medium' | 'Low';
  supporting_evidence: string;
  validation_needed: string;
}