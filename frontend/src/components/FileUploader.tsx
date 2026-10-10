import React, { useState } from 'react';
import { Upload, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import { DocumentMetadata } from '../types';

interface FileUploaderProps {
  onUploadSuccess: (doc: DocumentMetadata) => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onUploadSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.pdf')) {
      setError('Please upload a valid PDF file.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const doc = await api.uploadPDF(file);
      onUploadSuccess(doc);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process and extract PDF content.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-xl p-8 text-center bg-slate-900/50 transition-all">
      <input
        type="file"
        accept=".pdf"
        id="pdf-upload"
        className="hidden"
        onChange={handleFileChange}
        disabled={loading}
      />
      <label htmlFor="pdf-upload" className="cursor-pointer flex flex-col items-center">
        {loading ? (
          <Loader2 className="h-10 w-10 text-indigo-400 animate-spin mb-3" />
        ) : (
          <Upload className="h-10 w-10 text-indigo-400 mb-3" />
        )}
        <span className="text-base font-semibold text-slate-200">
          {loading ? 'Extracting & Indexing PDF...' : 'Click to upload research paper (PDF)'}
        </span>
        <span className="text-xs text-slate-400 mt-1">Supports searchable & digital PDFs up to 25MB</span>
      </label>

      {error && (
        <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg flex items-center space-x-2 text-rose-400 text-sm justify-center">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};