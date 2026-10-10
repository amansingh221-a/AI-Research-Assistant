import React from 'react';
import { BookOpen } from 'lucide-react';
import { Citation } from '../types';

interface CitationCardProps {
  citation: Citation;
}

export const CitationCard: React.FC<CitationCardProps> = ({ citation }) => {
  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-lg p-3 text-xs text-slate-300 mt-2">
      <div className="flex items-center justify-between mb-1 text-indigo-400 font-semibold">
        <span className="flex items-center space-x-1">
          <BookOpen className="h-3.5 w-3.5" />
          <span>{citation.document_name}</span>
        </span>
        <span className="bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded">
          Page {citation.page_number}
        </span>
      </div>
      <p className="italic text-slate-400 border-l-2 border-indigo-500/50 pl-2 mt-1">
        "{citation.excerpt}"
      </p>
    </div>
  );
};