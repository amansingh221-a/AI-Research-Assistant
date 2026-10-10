import React, { useState, useEffect } from 'react';
import { FileText, Send, Sparkles, BookOpen, AlertCircle, RefreshCw } from 'lucide-react';
import { DocumentMetadata, StructuredSummary, ChatMessage } from '../types';
import { api } from '../services/api';
import { CitationCard } from '../components/CitationCard';

interface DocumentWorkspaceProps {
  document: DocumentMetadata;
}

export const DocumentWorkspace: React.FC<DocumentWorkspaceProps> = ({ document }) => {
  const [summary, setSummary] = useState<StructuredSummary | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [summaryLength, setSummaryLength] = useState('standard');
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => {
    fetchSummary('standard');
  }, [document.id]);

  const fetchSummary = async (len: string) => {
    setLoadingSummary(true);
    try {
      const data = await api.getSummary(document.id, len);
      setSummary(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingSummary(false);
    }
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || chatLoading) return;

    const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', content: question };
    setChatHistory((prev) => [...prev, userMsg]);
    setQuestion('');
    setChatLoading(true);

    try {
      const res = await api.askQuestion(document.id, question);
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.answer,
        citations: res.citations,
        is_grounded: res.is_grounded
      };
      setChatHistory((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        { id: Date.now().toString(), role: 'assistant', content: 'Failed to retrieve answer from AI service.' }
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-6rem)]">
      {/* Left: Summary Section */}
      <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl flex flex-col overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center space-x-2">
            <FileText className="h-5 w-5 text-indigo-400" />
            <h2 className="font-semibold text-white truncate max-w-md">{document.filename}</h2>
          </div>
          <div className="flex items-center space-x-2">
            {['short', 'standard', 'detailed'].map((type) => (
              <button
                key={type}
                onClick={() => { setSummaryLength(type); fetchSummary(type); }}
                className={`px-2.5 py-1 text-xs rounded-md capitalize font-medium ${
                  summaryLength === type ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-slate-300 text-sm">
          {loadingSummary ? (
            <div className="flex flex-col items-center justify-center h-64 space-y-3">
              <RefreshCw className="h-8 w-8 text-indigo-400 animate-spin" />
              <p className="text-slate-400">Generating structured evidence summary...</p>
            </div>
          ) : summary ? (
            <>
              <div>
                <h3 className="text-lg font-bold text-white">{summary.paper_title}</h3>
                <p className="text-xs text-slate-400 mt-1">Authors: {summary.authors} | Year: {summary.publication_year}</p>
              </div>

              <div className="bg-slate-800/50 border border-slate-700/50 p-4 rounded-lg">
                <h4 className="font-semibold text-indigo-400 mb-1">Executive Summary</h4>
                <p>{summary.executive_summary}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-800/30 p-3 rounded-lg border border-slate-800">
                  <span className="text-xs text-slate-500 font-bold uppercase">Methodology</span>
                  <p className="mt-1 font-medium text-slate-200">{summary.methodology}</p>
                </div>
                <div className="bg-slate-800/30 p-3 rounded-lg border border-slate-800">
                  <span className="text-xs text-slate-500 font-bold uppercase">Dataset / Sample</span>
                  <p className="mt-1 font-medium text-slate-200">{summary.dataset_or_sample}</p>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-2">Important Findings</h4>
                <ul className="list-disc pl-5 space-y-1 text-slate-300">
                  {summary.important_findings?.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-rose-400 mb-2">Acknowledged Limitations</h4>
                <ul className="list-disc pl-5 space-y-1 text-slate-300">
                  {summary.limitations?.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            </>
          ) : (
            <p className="text-slate-400">No summary generated.</p>
          )}
        </div>
      </div>

      {/* Right: RAG Q&A Chat */}
      <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl flex flex-col overflow-hidden">
        <div className="p-4 border-b border-slate-800 bg-slate-900/80 flex items-center space-x-2">
          <Sparkles className="h-5 w-5 text-indigo-400" />
          <h3 className="font-semibold text-white">Ask Grounded Questions</h3>
        </div>

        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          {chatHistory.length === 0 ? (
            <div className="text-center text-slate-500 mt-12 text-xs">
              <p>Ask anything about this document.</p>
              <p className="mt-1 italic">"What methodology did the authors use?"</p>
            </div>
          ) : (
            chatHistory.map((msg) => (
              <div
                key={msg.id}
                className={`p-3 rounded-lg max-w-[90%] text-sm ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white ml-auto'
                    : 'bg-slate-800 text-slate-200 mr-auto border border-slate-700'
                }`}
              >
                <p>{msg.content}</p>
                {msg.citations?.map((c, i) => (
                  <CitationCard key={i} citation={c} />
                ))}
              </div>
            ))
          )}
        </div>

        <form onSubmit={handleAsk} className="p-3 border-t border-slate-800 bg-slate-900 flex space-x-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask question with citations..."
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={chatLoading}
            className="bg-indigo-600 hover:bg-indigo-500 text-white p-2 rounded-lg transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
};