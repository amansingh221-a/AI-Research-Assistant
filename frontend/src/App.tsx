import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { FileUploader } from './components/FileUploader';
import { DocumentWorkspace } from './pages/DocumentWorkspace';
import { api } from './services/api';
import { DocumentMetadata } from './types';
import { FileText, Layers, GitCompare, FileCode, Search } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [aiConfigured, setAiConfigured] = useState(false);
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);

  useEffect(() => {
    checkHealth();
    loadDocuments();
  }, []);

  const checkHealth = async () => {
    try {
      const data = await api.checkHealth();
      setAiConfigured(data.ai_configured);
    } catch {
      setAiConfigured(false);
    }
  };

  const loadDocuments = async () => {
    try {
      const docs = await api.getDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} aiConfigured={aiConfigured} />

      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-indigo-900/40 to-slate-900 border border-indigo-500/20 rounded-2xl p-6">
              <h1 className="text-2xl font-bold text-white">AI Research Assistant Workspace</h1>
              <p className="text-slate-400 text-sm mt-1">Upload papers, extract structured evidence, and ask grounded questions.</p>
            </div>

            <FileUploader onUploadSuccess={(doc) => { setDocuments([doc, ...documents]); setSelectedDoc(doc); setActiveTab('workspace'); }} />

            <div>
              <h2 className="text-lg font-semibold text-white mb-3">Uploaded Documents</h2>
              {documents.length === 0 ? (
                <p className="text-sm text-slate-500">No documents uploaded yet.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      onClick={() => { setSelectedDoc(doc); setActiveTab('workspace'); }}
                      className="bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-xl p-4 cursor-pointer transition-all"
                    >
                      <div className="flex items-center space-x-3">
                        <FileText className="h-6 w-6 text-indigo-400" />
                        <div className="truncate">
                          <h3 className="font-medium text-white truncate">{doc.filename}</h3>
                          <p className="text-xs text-slate-400">{doc.page_count} pages</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'workspace' && selectedDoc && (
          <DocumentWorkspace document={selectedDoc} />
        )}

        {activeTab === 'settings' && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h2 className="text-xl font-bold text-white">Application Configuration</h2>
            <p className="text-slate-400 text-sm">AI status: {aiConfigured ? 'Connected' : 'Missing API Key'}</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;