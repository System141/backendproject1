import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import Layout from '@/components/Layout';
import Link from 'next/link';

export default function ResetPassword() {
  const router = useRouter();
  const { token } = router.query;
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    setIsSubmitting(true);
    setMessage('');
    setError('');
    
    try {
      const res: any = await api.post('/api/auth/reset-password', { 
        token: token as string, 
        new_password: password 
      });
      setMessage(res.message || 'Password reset successfully.');
      setTimeout(() => router.push('/login'), 3000);
    } catch (err: any) {
      setError(err.message || 'An error occurred. The token might be expired or invalid.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-md mx-auto mt-10">
        <h1 className="text-3xl font-bold mb-6 text-center">Reset Password</h1>
        
        {message ? (
          <div className="bg-green-50 text-green-700 p-6 rounded border border-green-200 text-center">
            <p className="mb-4">{message}</p>
            <Link href="/login" className="text-blue-600 hover:underline font-medium">Go to Login</Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="bg-white shadow-sm border rounded-lg p-6 space-y-4">
            {error && (
              <div className="bg-red-50 text-red-700 p-4 rounded border border-red-200 text-sm">
                {error}
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
              <input 
                type="password" 
                className="w-full border rounded px-4 py-2" 
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                required 
                minLength={6}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
              <input 
                type="password" 
                className="w-full border rounded px-4 py-2" 
                value={confirmPassword} 
                onChange={e => setConfirmPassword(e.target.value)} 
                required 
                minLength={6}
              />
            </div>
            
            <button 
              type="submit" 
              disabled={isSubmitting || !token}
              className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-blue-400"
            >
              {isSubmitting ? 'Resetting...' : 'Reset Password'}
            </button>
            
            {!token && (
              <p className="text-red-500 text-xs mt-2 text-center">No token found in URL.</p>
            )}
          </form>
        )}
      </div>
    </Layout>
  );
}
