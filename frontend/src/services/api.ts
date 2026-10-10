import axios from 'axios';
import { DocumentMetadata, StructuredSummary, ChatMessage, ResearchGap } from '../types';

const API_BASE = 'http://localhost:8000/api';

export const api = {
  checkHealth: async () => {
    const res = await axios.get(`${API_BASE}/health`);
    return res.data;
  },
  
  uploadPDF: async (file: File): Promise<DocumentMetadata> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await axios.post(`${API_BASE}/documents/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },

  getDocuments: async (): Promise<DocumentMetadata[]> => {
    const res = await axios.get(`${API_BASE}/documents`);
    return res.data;
  },

  deleteDocument: async (docId: string): Promise<void> => {
    await axios.delete(`${API_BASE}/documents/${docId}`);
  },

  getSummary: async (docId: string, lengthType: string = 'standard'): Promise<StructuredSummary> => {
    const res = await axios.post(`${API_BASE}/documents/${docId}/summary`, { length_type: lengthType });
    return res.data;
  },

  askQuestion: async (docId: string, question: string) => {
    const res = await axios.post(`${API_BASE}/documents/${docId}/chat`, { question });
    return res.data;
  },

  comparePapers: async (documentIds: string[]) => {
    const res = await axios.post(`${API_BASE}/compare`, { document_ids: documentIds });
    return res.data;
  },

  analyzeGaps: async (documentIds: string[]) => {
    const res = await axios.post(`${API_BASE}/research-gaps`, { document_ids: documentIds });
    return res.data;
  },

  generateReport: async (title: string, documentIds: string[]) => {
    const res = await axios.post(`${API_BASE}/reports`, { title, document_ids: documentIds });
    return res.data;
  }
};