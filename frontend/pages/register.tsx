import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';

export default function Register() {
  const { t } = useTranslation();
  const { register } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ name: '', email: '', password: '', phone: '', role: 'buyer', accepted_terms: false, accepted_privacy: false, marketing_consent: false });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try { await register(form); router.push('/'); }
    catch { setError(t('error')); }
  };

  return (
    <Layout>
      <div className="max-w-md mx-auto mt-10">
        <h1 className="text-2xl font-bold mb-6">{t('register_title')}</h1>
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input className="w-full border rounded px-4 py-2" placeholder={t('name')} value={form.name} onChange={e => setForm({...form, name: e.target.value})} required />
          <input className="w-full border rounded px-4 py-2" type="email" placeholder={t('email')} value={form.email} onChange={e => setForm({...form, email: e.target.value})} required />
          <input className="w-full border rounded px-4 py-2" type="password" placeholder={t('password')} value={form.password} onChange={e => setForm({...form, password: e.target.value})} required />
          <input className="w-full border rounded px-4 py-2" placeholder={t('phone')} value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} />
          <select className="w-full border rounded px-4 py-2" value={form.role} onChange={e => setForm({...form, role: e.target.value})}>
            <option value="buyer">{t('role')} - Buyer</option>
            <option value="seller">Seller</option>
          </select>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={form.accepted_terms} onChange={e => setForm({...form, accepted_terms: e.target.checked})} required />
            {t('accept_terms')}
          </label>
          <button className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700" type="submit">{t('submit')}</button>
        </form>
      </div>
    </Layout>
  );
}
