import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import Layout from '@/components/Layout';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';

interface Auction {
  id: string; title: string; current_price: number; end_time: string; status: string;
  start_price: number; category_id: number; brand?: string; model?: string; year?: number;
}

export default function AuctionsPage() {
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
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white rounded-2xl p-8 sm:p-12 mb-8">
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight mb-3">{t('nav_auctions')}</h1>
        <p className="text-gray-300 text-lg max-w-2xl">{t('hero_btn1')}</p>
      </div>

      <div className="flex flex-wrap gap-4 mb-8">
        <input
          className="flex-1 min-w-[200px] border rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none"
          placeholder={t('search')}
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select
          className="w-44 border rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none bg-white"
          value={category}
          onChange={e => setCategory(e.target.value)}
        >
          <option value="">{t('categories')}</option>
          <option value="1">{t('nav_vehicles')}</option>
          <option value="2">{t('nav_equipment')}</option>
          <option value="3">{t('nav_general')}</option>
        </select>
        <Link href="/auctions/new" className="bg-red-600 hover:bg-red-500 text-white font-bold px-5 py-2.5 rounded-lg transition text-sm">
          {t('nav_create')}
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {auctions.length === 0 && (
          <div className="col-span-full text-center py-16 text-gray-500">
            <p className="text-lg">{t('no_results')}</p>
          </div>
        )}
        {auctions.map(a => (
          <Link key={a.id} href={`/auctions/${a.id}`} className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition p-6">
            <h2 className="text-lg font-semibold mb-2 text-gray-900">{a.title}</h2>
            <p className="text-2xl font-bold text-blue-600">${a.current_price.toFixed(2)}</p>
            <p className="text-sm text-gray-500 mt-2">{t('end_time')}: {new Date(a.end_time).toLocaleString()}</p>
            {a.brand && <p className="text-sm text-gray-500">{a.brand} {a.model} ({a.year})</p>}
            <span className={`inline-block mt-2 px-2.5 py-1 text-xs font-semibold rounded-full ${
              a.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
            }`}>{a.status}</span>
          </Link>
        ))}
      </div>
    </Layout>
  );
}