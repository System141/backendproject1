import { useState } from 'react';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';

export default function CreateAuction() {
  const { t } = useTranslation();
  const router = useRouter();
  const { user } = useAuth();
  const [form, setForm] = useState({
    title: '', description: '', category_id: 1, start_price: 0, min_increment: 10,
    end_time: '', brand: '', model: '', year: '', mileage: '',
  });
  const [error, setError] = useState('');

  if (!user || (user.role !== 'seller' && user.role !== 'corporate_seller')) {
    return <Layout><p className="text-red-500">Only sellers can create auctions.</p></Layout>;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/api/auctions', { ...form, year: form.year ? parseInt(form.year) : null, mileage: form.mileage ? parseInt(form.mileage) : null });
      router.push('/');
    } catch { setError(t('error')); }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">{t('nav_create')}</h1>
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input className="w-full border rounded px-4 py-2" placeholder={t('name')} value={form.title} onChange={e => setForm({...form, title: e.target.value})} required />
          <textarea className="w-full border rounded px-4 py-2" rows={4} placeholder="Description" value={form.description} onChange={e => setForm({...form, description: e.target.value})} required />
          <div className="grid grid-cols-2 gap-4">
            <input className="border rounded px-4 py-2" type="number" step="0.01" placeholder="Start Price" value={form.start_price} onChange={e => setForm({...form, start_price: parseFloat(e.target.value)})} required />
            <input className="border rounded px-4 py-2" type="number" step="0.01" placeholder="Min Increment" value={form.min_increment} onChange={e => setForm({...form, min_increment: parseFloat(e.target.value)})} required />
            <input className="border rounded px-4 py-2" type="datetime-local" placeholder="End Time" value={form.end_time} onChange={e => setForm({...form, end_time: e.target.value})} required />
            <input className="border rounded px-4 py-2" placeholder="Brand" value={form.brand} onChange={e => setForm({...form, brand: e.target.value})} />
            <input className="border rounded px-4 py-2" placeholder="Model" value={form.model} onChange={e => setForm({...form, model: e.target.value})} />
            <input className="border rounded px-4 py-2" type="number" placeholder="Year" value={form.year} onChange={e => setForm({...form, year: e.target.value})} />
            <input className="border rounded px-4 py-2" type="number" placeholder="Mileage (km)" value={form.mileage} onChange={e => setForm({...form, mileage: e.target.value})} />
          </div>
          <button className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700" type="submit">{t('submit')}</button>
        </form>
      </div>
    </Layout>
  );
}