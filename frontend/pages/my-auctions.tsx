import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import Layout from '@/components/Layout';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';

interface Auction { id: string; title: string; current_price: number; status: string; end_time: string; created_at: string; }

export default function MyAuctions() {
  const { t } = useTranslation();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [auctions, setAuctions] = useState<Auction[]>([]);

  useEffect(() => {
    if (!loading && (!user || (user.role !== 'seller' && user.role !== 'corporate_seller'))) router.push('/');
    if (user) api.get<Auction[]>('/api/auctions/my').then(setAuctions).catch(console.error);
  }, [user, loading]);

  if (loading || !user) return <Layout><p>{t('loading')}</p></Layout>;

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-6">{t('nav_my_auctions')}</h1>
      <div className="space-y-4">
        {auctions.map(a => (
          <Link key={a.id} href={`/auctions/${a.id}`} className="block bg-white rounded-lg shadow p-4 hover:shadow-md">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="font-semibold">{a.title}</h2>
                <p className="text-sm text-gray-500">{new Date(a.created_at).toLocaleDateString()}</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-blue-600">${a.current_price.toFixed(2)}</p>
                <span className={`inline-block px-2 py-1 text-xs rounded ${a.status === 'active' ? 'bg-green-100 text-green-800' : a.status === 'pending_approval' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-600'}`}>{a.status}</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </Layout>
  );
}