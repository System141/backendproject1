import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';

export default function Login() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try { await login(email, password); router.push('/'); }
    catch { setError(t('error')); }
  };

  return (
    <Layout>
      <div className="max-w-md mx-auto mt-10">
        <h1 className="text-2xl font-bold mb-6">{t('login_title')}</h1>
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input className="w-full border rounded px-4 py-2" type="email" placeholder={t('email')} value={email} onChange={e => setEmail(e.target.value)} required />
          <input className="w-full border rounded px-4 py-2" type="password" placeholder={t('password')} value={password} onChange={e => setPassword(e.target.value)} required />
          <button className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700" type="submit">{t('submit')}</button>
        </form>
      </div>
    </Layout>
  );
}
