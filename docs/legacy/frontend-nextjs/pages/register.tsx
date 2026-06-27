import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';
import Link from 'next/link';

export default function Register() {
  const { t } = useTranslation();
  const { register } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    phone: '',
    role: 'buyer' as string,
    accepted_terms: false,
    accepted_privacy: false,
    marketing_consent: false,
  });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (form.password !== form.confirmPassword) {
      setError(t('error_passwords_mismatch') || 'Passwords do not match');
      return;
    }
    if (form.password.length < 6) {
      setError(t('error_password_too_short') || 'Password must be at least 6 characters');
      return;
    }
    if (!form.accepted_terms || !form.accepted_privacy) {
      setError(t('error_accept_terms') || 'You must accept the terms and privacy policy');
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        name: form.name,
        email: form.email,
        password: form.password,
        phone: form.phone || null,
        role: form.role,
        accepted_terms: form.accepted_terms,
        accepted_privacy: form.accepted_privacy,
        marketing_consent: form.marketing_consent,
      });
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
        <h1 className="text-2xl font-bold mb-6">{t('register_title')}</h1>
        {error && <p className="text-red-500 mb-4 p-3 bg-red-50 rounded border border-red-200">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4 bg-white shadow-sm border rounded-lg p-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('register_name')}</label>
            <input
              className="w-full border rounded px-4 py-2"
              placeholder={t('register_name')}
              value={form.name}
              onChange={e => setForm({...form, name: e.target.value})}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('email')}</label>
            <input
              className="w-full border rounded px-4 py-2"
              type="email"
              placeholder={t('email')}
              value={form.email}
              onChange={e => setForm({...form, email: e.target.value})}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('password')}</label>
            <input
              className="w-full border rounded px-4 py-2"
              type="password"
              placeholder={t('password')}
              value={form.password}
              onChange={e => setForm({...form, password: e.target.value})}
              required
              minLength={6}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('register_confirm')}</label>
            <input
              className="w-full border rounded px-4 py-2"
              type="password"
              placeholder={t('register_confirm')}
              value={form.confirmPassword}
              onChange={e => setForm({...form, confirmPassword: e.target.value})}
              required
              minLength={6}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('register_phone')}</label>
            <input
              className="w-full border rounded px-4 py-2"
              placeholder={t('register_phone')}
              value={form.phone}
              onChange={e => setForm({...form, phone: e.target.value})}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('register_type')}</label>
            <select
              className="w-full border rounded px-4 py-2"
              value={form.role}
              onChange={e => setForm({...form, role: e.target.value})}
            >
              <option value="buyer">{t('register_type1')}</option>
              <option value="seller">{t('register_type2')}</option>
              <option value="corporate_seller">{t('register_type3')}</option>
            </select>
          </div>

          <div className="space-y-2 pt-2 border-t">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={form.accepted_terms}
                onChange={e => setForm({...form, accepted_terms: e.target.checked})}
                className="mt-1"
                required
              />
              <span className="text-sm text-gray-600">{t('register_terms')}</span>
            </label>
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={form.accepted_privacy}
                onChange={e => setForm({...form, accepted_privacy: e.target.checked})}
                className="mt-1"
                required
              />
              <span className="text-sm text-gray-600">{t('register_privacy')}</span>
            </label>
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={form.marketing_consent}
                onChange={e => setForm({...form, marketing_consent: e.target.checked})}
                className="mt-1"
              />
              <span className="text-sm text-gray-600">{t('register_marketing')}</span>
            </label>
          </div>

          <button
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-blue-400"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? t('loading') : t('register_btn')}
          </button>

          <p className="text-center text-sm text-gray-500 mt-4">
            {t('auth_title')}?{' '}
            <Link href="/login" className="text-blue-600 hover:underline">{t('auth_register_link')}</Link>
          </p>
        </form>
      </div>
    </Layout>
  );
}