import React, { useState } from 'react';
import { billingAPI } from '../api';
import { CreditCard, ExternalLink, CheckCircle } from 'lucide-react';

export default function StripeBilling() {
  const [loading, setLoading] = useState(false);

  const handleManageBilling = async () => {
    setLoading(true);
    try {
      const { data } = await billingAPI.createSession();
      // Redirect to Stripe Checkout or Billing Portal
      window.location.href = data.url; 
    } catch (err) {
      alert("Failed to connect to billing service.");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto mt-10 p-8 bg-brand-800 rounded-xl border border-slate-700">
      <div className="flex items-center gap-4 mb-6">
        <div className="p-3 bg-brand-600/20 rounded-lg">
          <CreditCard className="text-brand-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Subscription & Billing</h2>
          <p className="text-slate-400 text-sm">Manage your plan and metered usage.</p>
        </div>
      </div>

      <div className="bg-brand-900 p-6 rounded-lg mb-8 border border-slate-700">
        <div className="flex justify-between items-center mb-4">
          <span className="text-slate-400">Current Plan</span>
          <span className="bg-green-500/10 text-green-500 text-xs px-2 py-1 rounded-full border border-green-500/20">Active</span>
        </div>
        <h3 className="text-2xl font-bold">Enterprise RAG <span className="text-sm font-normal text-slate-500">/ metered</span></h3>
        
        <ul className="mt-4 space-y-2 text-sm text-slate-300">
          <li className="flex items-center gap-2"><CheckCircle size={14} className="text-brand-600" /> Isolated Qdrant Namespace</li>
          <li className="flex items-center gap-2"><CheckCircle size={14} className="text-brand-600" /> $0.01 per 1k Search Queries</li>
          <li className="flex items-center gap-2"><CheckCircle size={14} className="text-brand-600" /> Unlimited Vector Storage</li>
        </ul>
      </div>

      <button 
        onClick={handleManageBilling}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 bg-white text-brand-900 p-4 rounded-lg font-bold hover:bg-slate-200 transition disabled:opacity-50"
      >
        {loading ? "Connecting..." : "Manage Billing in Stripe"}
        <ExternalLink size={18} />
      </button>
      
      <p className="mt-4 text-xs text-center text-slate-500">
        Securely processed by Stripe. Your data isolation is guaranteed by Bravado Solutions' multi-tenant architecture.
      </p>
    </div>
  );
}