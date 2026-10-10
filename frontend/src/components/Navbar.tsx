import React from 'react';
import { FileText, Cpu, Settings } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  aiConfigured: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, aiConfigured }) => {
  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('landing')}>
          <div className="p-2 bg-indigo-600 rounded-lg">
            <FileText className="h-6 w-6 text-white" />
          </div>
          <div>
            <span className="font-bold text-lg tracking-tight">ResearchMate AI</span>
            <span className="block text-xs text-slate-400">Academic Paper Intelligence</span>
          </div>
        </div>

        <nav className="flex items-center space-x-1">
          {['dashboard', 'library', 'compare', 'gaps', 'report'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-2 rounded-md text-sm font-medium capitalize transition-colors ${
                activeTab === tab ? 'bg-slate-800 text-indigo-400' : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>

        <div className="flex items-center space-x-3">
          <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
            aiConfigured ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
          }`}>
            <Cpu className="h-3.5 w-3.5" />
            <span>{aiConfigured ? 'AI Ready' : 'Setup Needed'}</span>
          </div>
          <button 
            onClick={() => setActiveTab('settings')}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
          >
            <Settings className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
};