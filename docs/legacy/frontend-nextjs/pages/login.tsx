import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';
import Link from 'next/link';

export default function Login() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');
    try {
      await login(email, password);
      router.push('/');
    } catch (err: any) {
      setError(err?.message || t('error'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-md mx-auto mt-10">
        <h1 className="text-2xl font-bold mb-6">{t('login_title')}</h1>
        {error && <p className="text-red-500 mb-4 p-3 bg-red-50 rounded border border-red-200">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4 bg-white shadow-sm border rounded-lg p-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('email')}</label>
            <input
              className="w-full border rounded px-4 py-2"
              type="email"
              placeholder={t('email')}
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('password')}</label>
            <input
              className="w-full border rounded px-4 py-2"
              type="password"
              placeholder={t('password')}
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="flex items-center justify-between text-sm">
            <Link href="/forgot-password" className="text-blue-600 hover:underline">
              {t('auth_forgot')}
            </Link>
          </div>

          <button
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-blue-400"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? t('loading') : t('auth_btn')}
          </button>

          <p className="text-center text-sm text-gray-500 mt-4">
            {t('register_title')}?{' '}
            <Link href="/register" className="text-blue-600 hover:underline">{t('nav_register')}</Link>
          </p>
        </form>
      </div>
    </Layout>
  );
}