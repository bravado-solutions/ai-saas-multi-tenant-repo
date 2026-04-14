import React, { useState } from 'react';
import { aiAPI } from '../api';
import { LogOut, Send, Database } from 'lucide-react';

export default function Dashboard() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const onSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await aiAPI.ask(query);
      setResults(data.context || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-64 bg-brand-800 p-6 flex flex-col justify-between border-r border-slate-700">
        <div>
          <h1 className="text-xl font-bold mb-8 flex items-center gap-2">
            <Database className="text-brand-600" /> Bravado AI
          </h1>
          <nav className="space-y-4">
            <button className="w-full text-left p-2 rounded bg-slate-700">RAG Dashboard</button>
            <button className="w-full text-left p-2 rounded hover:bg-slate-700">Knowledge Base</button>
          </nav>
        </div>
        <button onClick={() => { localStorage.clear(); window.location.reload(); }} className="flex items-center gap-2 text-slate-400 hover:text-white transition">
          <LogOut size={18} /> Logout
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <div className="p-8 overflow-y-auto flex-1">
          <div className="max-w-3xl mx-auto space-y-6">
            {results.map((res, i) => (
              <div key={i} className="p-4 bg-brand-800 rounded-lg border border-slate-700">
                <p className="text-slate-300">{res.text_content}</p>
                <span className="text-xs text-brand-600 mt-2 block">Source: Qdrant Vector DB</span>
              </div>
            ))}
          </div>
        </div>

        {/* Input Bar */}
        <div className="p-8 border-t border-slate-700 bg-brand-900">
          <form onSubmit={onSearch} className="max-w-3xl mx-auto flex gap-4">
            <input className="flex-1 bg-brand-800 border border-slate-700 p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600" placeholder="Query your tenant data..." value={query} onChange={e => setQuery(e.target.value)} />
            <button type="submit" disabled={loading} className="bg-brand-600 px-6 py-4 rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50">
              <Send size={20} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}