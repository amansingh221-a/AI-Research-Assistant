import os
import uuid
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sqlite3

from app.database import get_db, init_db, STORAGE_DIR
from app.schemas import (
    DocumentMetadata, SummaryRequest, ChatRequest, ChatResponse,
    ComparisonRequest, ResearchGapRequest, ReportRequest
)
from app.services.pdf_service import PDFProcessor
from app.services.retrieval_service import SimpleBM25Retriever
from app.services.ai_service import AIService
from app.services.report_service import ReportGenerator

app = FastAPI(title="ResearchMate AI Backend", version="1.0.0")

# CORS Setup
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_service = AIService()

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "ai_configured": ai_service.is_configured(),
        "ai_provider": ai_service.provider,
        "storage_ready": STORAGE_DIR.exists()
    }

@app.post("/api/documents/upload", response_model=DocumentMetadata)
async def upload_document(file: UploadFile = File(...), db: sqlite3.Connection = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    MAX_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", 25))
    contents = await file.read()
    if len(contents) > MAX_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum size limit of {MAX_MB}MB.")

    doc_id = str(uuid.uuid4())
    safe_ext = ".pdf"
    stored_filename = f"{doc_id}{safe_ext}"
    upload_dir = STORAGE_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / stored_filename

    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        chunks, page_count, is_scanned = PDFProcessor.extract_and_chunk(file_path)
        status = "processed" if not is_scanned else "scanned_pdf_warning"
        err_msg = "OCR recommended: Document contains minimal selectable text." if is_scanned else None

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO documents (id, filename, stored_filename, file_size, page_count, is_scanned, processing_status, error_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (doc_id, file.filename, stored_filename, len(contents), page_count, 1 if is_scanned else 0, status, err_msg)
        )

        for chunk in chunks:
            cursor.execute(
                "INSERT INTO chunks (id, document_id, chunk_index, page_number, content, token_estimate) VALUES (?, ?, ?, ?, ?, ?)",
                (chunk["id"], doc_id, chunk["chunk_index"], chunk["page_number"], chunk["content"], chunk["token_estimate"])
            )

        db.commit()
        return DocumentMetadata(
            id=doc_id,
            filename=file.filename,
            file_size=len(contents),
            page_count=page_count,
            is_scanned=is_scanned,
            processing_status=status,
            error_message=err_msg,
            created_at=str(uuid.uuid1())
        )
    except Exception as e:
        db.rollback()
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@app.get("/api/documents")
def list_documents(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, filename, file_size, page_count, is_scanned, processing_status, error_message, created_at FROM documents ORDER BY created_at DESC")
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT stored_filename FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found.")

    file_path = STORAGE_DIR / "uploads" / row["stored_filename"]
    if file_path.exists():
        file_path.unlink()

    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    db.commit()
    return {"message": "Document deleted successfully."}

@app.post("/api/documents/{doc_id}/summary")
async def generate_summary(doc_id: str, req: SummaryRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT content FROM chunks WHERE document_id = ? ORDER BY chunk_index ASC LIMIT 20", (doc_id,))
    rows = cursor.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="Document text content not found.")

    full_text = "\n".join([r["content"] for r in rows])
    summary_data = await ai_service.generate_summary(full_text, req.length_type)

    summary_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO summaries (id, document_id, length_type, summary_json) VALUES (?, ?, ?, ?)",
        (summary_id, doc_id, req.length_type, json.dumps(summary_data))
    )
    db.commit()
    return summary_data

@app.post("/api/documents/{doc_id}/chat", response_model=ChatResponse)
async def chat_with_document(doc_id: str, req: ChatRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT filename FROM documents WHERE id = ?", (doc_id,))
    doc_row = cursor.fetchone()
    if not doc_row:
        raise HTTPException(status_code=404, detail="Document not found.")

    cursor.execute("SELECT id, page_number, content FROM chunks WHERE document_id = ?", (doc_id,))
    chunks = [dict(r) for r in cursor.fetchall()]
    if not chunks:
        raise HTTPException(status_code=400, detail="Document has no text available for retrieval.")

    relevant_chunks = SimpleBM25Retriever.retrieve(chunks, req.question, top_k=4)
    response = await ai_service.answer_question(req.question, relevant_chunks, doc_row["filename"], doc_id)

    # Save chat turn
    cursor.execute("INSERT INTO chat_history (id, document_id, role, content) VALUES (?, ?, ?, ?)",
                   (str(uuid.uuid4()), doc_id, "user", req.question))
    cursor.execute("INSERT INTO chat_history (id, document_id, role, content, citations_json) VALUES (?, ?, ?, ?, ?)",
                   (str(uuid.uuid4()), doc_id, "assistant", response.answer, json.dumps([c.model_dump() for c in response.citations])))
    db.commit()
    return response

@app.post("/api/compare")
async def compare_documents(req: ComparisonRequest, db: sqlite3.Connection = Depends(get_db)):
    if len(req.document_ids) < 2:
        raise HTTPException(status_code=400, detail="At least two documents are required for comparison.")

    cursor = db.cursor()
    papers_data = []
    for d_id in req.document_ids:
        cursor.execute("SELECT filename FROM documents WHERE id = ?", (d_id,))
        doc = cursor.fetchone()
        cursor.execute("SELECT summary_json FROM summaries WHERE document_id = ? ORDER BY created_at DESC LIMIT 1", (d_id,))
        sum_row = cursor.fetchone()
        
        summary_val = json.loads(sum_row["summary_json"]) if sum_row else {"paper_title": doc["filename"]}
        papers_data.append(summary_val)

    comparison_result = await ai_service.compare_papers(papers_data)
    return comparison_result

@app.post("/api/research-gaps")
async def analyze_research_gaps(req: ResearchGapRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    papers_data = []
    for d_id in req.document_ids:
        cursor.execute("SELECT summary_json FROM summaries WHERE document_id = ? ORDER BY created_at DESC LIMIT 1", (d_id,))
        sum_row = cursor.fetchone()
        if sum_row:
            papers_data.append(json.loads(sum_row["summary_json"]))

    return await ai_service.analyze_gaps(papers_data)

@app.post("/api/reports")
async def generate_report(req: ReportRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    doc_names = []
    summaries = []
    for d_id in req.document_ids:
        cursor.execute("SELECT filename FROM documents WHERE id = ?", (d_id,))
        row = cursor.fetchone()
        if row:
            doc_names.append(row["filename"])
        cursor.execute("SELECT summary_json FROM summaries WHERE document_id = ? ORDER BY created_at DESC LIMIT 1", (d_id,))
        sum_row = cursor.fetchone()
        if sum_row:
            summaries.append(json.loads(sum_row["summary_json"]))

    combined_summary = summaries[0] if summaries else {}
    gap_data = await ai_service.analyze_gaps(summaries)
    
    markdown_content = ReportGenerator.create_markdown_report(req.title, doc_names, combined_summary, gap_data)

    report_id = str(uuid.uuid4())
    reports_dir = STORAGE_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{report_id}.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    cursor.execute("INSERT INTO reports (id, title, report_type, document_ids, content_markdown) VALUES (?, ?, ?, ?, ?)",
                   (report_id, req.title, req.report_type, json.dumps(req.document_ids), markdown_content))
    db.commit()

    return {"report_id": report_id, "title": req.title, "markdown": markdown_content}

@app.get("/api/reports/{report_id}/download")
def download_report(report_id: str, format: str = Query("md")):
    report_path = STORAGE_DIR / "reports" / f"{report_id}.md"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found.")

    if format == "txt":
        return FileResponse(report_path, media_type="text/plain", filename=f"report_{report_id}.txt")
    return FileResponse(report_path, media_type="text/markdown", filename=f"report_{report_id}.md")