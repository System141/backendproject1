import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import Layout from '@/components/Layout';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';

interface Auction {
  id: string; title: string; current_price: number; end_time: string; status: string;
  start_price: number; category_id: number;
}

export default function GeneralPage() {
  const { t } = useTranslation();
  const [auctions, setAuctions] = useState<Auction[]>([]);

  useEffect(() => {
    api.get<Auction[]>('/api/auctions?category_id=3')
      .then(setAuctions)
      .catch(console.error);
  }, []);

  return (
    <Layout>
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white rounded-2xl p-8 sm:p-12 mb-8">
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight mb-3">{t('nav_general')}</h1>
        <p className="text-gray-300 text-lg max-w-2xl">{t('cat_general_desc')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {auctions.length === 0 && (
          <div className="col-span-full text-center py-12 text-gray-500">
            <p className="text-lg">{t('no_results')}</p>
          </div>
        )}
        {auctions.map(a => (
          <Link key={a.id} href={`/auctions/${a.id}`} className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition p-6">
            <h2 className="text-lg font-semibold mb-2 text-gray-900">{a.title}</h2>
            <p className="text-2xl font-bold text-blue-600">${a.current_price.toFixed(2)}</p>
            <p className="text-sm text-gray-500 mt-2">{t('end_time')}: {new Date(a.end_time).toLocaleString()}</p>
            <span className={`inline-block mt-2 px-2.5 py-1 text-xs font-semibold rounded-full ${
              a.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
            }`}>{a.status}</span>
          </Link>
        ))}
      </div>
    </Layout>
  );
}