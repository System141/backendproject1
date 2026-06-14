import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import Layout from '@/components/Layout';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';

interface Auction {
  id: string; title: string; current_price: number; end_time: string; status: string;
  start_price: number; category_id: number; brand?: string; model?: string; year?: number;
}

export default function Home() {
  const { t } = useTranslation();
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');

  useEffect(() => {
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (category) params.set('category_id', category);
    api.get<Auction[]>(`/api/auctions?${params}`).then(setAuctions).catch(console.error);
  }, [search, category]);

  return (
    <Layout>
      <div className="flex gap-4 mb-6">
        <input className="flex-1 border rounded px-4 py-2" placeholder={t('search')} value={search} onChange={e => setSearch(e.target.value)} />
        <input className="w-40 border rounded px-4 py-2" placeholder={t('categories')} value={category} onChange={e => setCategory(e.target.value)} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {auctions.map(a => (
          <Link key={a.id} href={`/auctions/${a.id}`} className="bg-white rounded-lg shadow p-6 hover:shadow-md transition">
            <h2 className="text-lg font-semibold mb-2">{a.title}</h2>
            <p className="text-2xl font-bold text-blue-600">${a.current_price.toFixed(2)}</p>
            <p className="text-sm text-gray-500 mt-2">{t('end_time')}: {new Date(a.end_time).toLocaleString()}</p>
            {a.brand && <p className="text-sm text-gray-500">{a.brand} {a.model} ({a.year})</p>}
            <span className={`inline-block mt-2 px-2 py-1 text-xs rounded ${a.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>{a.status}</span>
          </Link>
        ))}
      </div>
    </Layout>
  );
}
