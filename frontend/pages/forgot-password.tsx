import { useState } from 'react';
import { api } from '@/lib/api';
import Layout from '@/components/Layout';
import Link from 'next/link';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setMessage('');
    setError('');
    
    try {
      const res: any = await api.post('/api/auth/forgot-password', { email });
      // In dev mode, the backend returns the reset_token directly for testing.
      if (res.reset_token) {
        setMessage(`Dev Mode: A reset token was generated. Go to /reset-password?token=${res.reset_token} to test it.`);
      } else {
        setMessage(res.message || 'If the email exists, a reset link has been sent.');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-md mx-auto mt-10">
        <h1 className="text-3xl font-bold mb-6 text-center">Forgot Password</h1>
        
        {message && (
          <div className="mb-4 bg-green-50 text-green-700 p-4 rounded border border-green-200 text-sm break-all">
            {message}
          </div>
        )}
        
        {error && (
          <div className="mb-4 bg-red-50 text-red-700 p-4 rounded border border-red-200 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white shadow-sm border rounded-lg p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
            <input 
              type="email" 
              className="w-full border rounded px-4 py-2" 
              value={email} 
              onChange={e => setEmail(e.target.value)} 
              required 
              placeholder="Enter your email"
            />
          </div>
          <button 
            type="submit" 
            disabled={isSubmitting}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-blue-400"
          >
            {isSubmitting ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>
        
        <div className="mt-4 text-center">
          <Link href="/login" className="text-blue-600 hover:underline text-sm">Back to Login</Link>
        </div>
      </div>
    </Layout>
  );
}
