import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api';
import { ShieldCheck } from 'lucide-react';

export default function Signup() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    companyName: ''
  });
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      await authAPI.signup(formData);
      alert("Account created successfully! Please login.");
      navigate('/login');
    } catch (err) {
      alert("Signup failed. That email might already be in use.");
    }
  };

  return (
    <div className="flex items-center justify-center h-screen bg-brand-900">
      <form onSubmit={handleSignup} className="p-8 bg-brand-800 rounded-lg shadow-2xl w-96 border border-slate-700">
        <div className="flex justify-center mb-4">
          <ShieldCheck size={40} className="text-brand-600" />
        </div>
        <h2 className="text-2xl font-bold mb-6 text-center">Create Bravado Account</h2>
        
        <label className="block text-sm text-slate-400 mb-1">Company / Organization</label>
        <input type="text" placeholder="e.g. Acme Corp" className="w-full p-3 mb-4 rounded bg-brand-900 border border-slate-700 focus:ring-1 focus:ring-brand-600 outline-none" 
          onChange={e => setFormData({...formData, companyName: e.target.value})} required />
        
        <label className="block text-sm text-slate-400 mb-1">Work Email</label>
        <input type="email" placeholder="name@company.com" className="w-full p-3 mb-4 rounded bg-brand-900 border border-slate-700 focus:ring-1 focus:ring-brand-600 outline-none" 
          onChange={e => setFormData({...formData, email: e.target.value})} required />
        
        <label className="block text-sm text-slate-400 mb-1">Password</label>
        <input type="password" placeholder="••••••••" className="w-full p-3 mb-6 rounded bg-brand-900 border border-slate-700 focus:ring-1 focus:ring-brand-600 outline-none" 
          onChange={e => setFormData({...formData, password: e.target.value})} required />
        
        <button type="submit" className="w-full bg-brand-600 p-3 rounded font-bold hover:bg-blue-700 transition duration-200">
          Create Tenant & Start
        </button>
        
        <p className="mt-6 text-center text-sm text-slate-400">
          Already have a workspace? <Link to="/login" className="text-brand-600 hover:underline">Log in</Link>
        </p>
      </form>
    </div>
  );
}