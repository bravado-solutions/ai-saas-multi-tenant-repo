import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const { data } = await authAPI.login({ email, password });
      localStorage.setItem('token', data.access_token);
      navigate('/dashboard');
    } catch (err) {
      alert("Login failed. Please check your credentials.");
    }
  };

  return (
    <div className="flex items-center justify-center h-screen bg-brand-900">
      <form onSubmit={handleLogin} className="p-8 bg-brand-800 rounded-lg shadow-xl w-96">
        <h2 className="text-2xl font-bold mb-6 text-center">Bravado Login</h2>
        <input type="email" placeholder="Email" className="w-full p-3 mb-4 rounded bg-brand-900 border border-slate-700" onChange={e => setEmail(e.target.value)} required />
        <input type="password" placeholder="Password" className="w-full p-3 mb-6 rounded bg-brand-900 border border-slate-700" onChange={e => setPassword(e.target.value)} required />
        <button type="submit" className="w-full bg-brand-600 p-3 rounded font-bold hover:bg-blue-700 transition">Enter Platform</button>
        <p className="mt-4 text-center text-sm text-slate-400">Don't have an account? <Link to="/signup" className="text-brand-600">Sign up</Link></p>
      </form>
    </div>
  );
}