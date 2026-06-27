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
  const [isLoadingAuctions, setIsLoadingAuctions] = useState(true);

  useEffect(() => {
    if (!loading && (!user || (user.role !== 'seller' && user.role !== 'corporate_seller'))) {
      router.push('/');
      return;
    }
    if (user) {
      api.get<Auction[]>('/api/auctions/my')
        .then(setAuctions)
        .catch(() => {})
        .finally(() => setIsLoadingAuctions(false));
    }
  }, [user, loading, router]);

  if (loading || !user) return <Layout><p className="p-6">{t('loading')}</p></Layout>;

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">{t('nav_my_auctions')}</h1>
          <Link
            href="/auctions/new"
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm font-medium transition"
          >
            {t('nav_create')}
          </Link>
        </div>

        {isLoadingAuctions ? (
          <p className="text-gray-500">{t('loading')}</p>
        ) : auctions.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-500 mb-4">{t('no_auctions') || 'No auctions found.'}</p>
            <Link
              href="/auctions/new"
              className="text-blue-600 hover:underline font-medium"
            >
              {t('nav_create')}
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {auctions.map(a => (
              <Link key={a.id} href={`/auctions/${a.id}`} className="block bg-white rounded-lg shadow p-4 hover:shadow-md transition">
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="font-semibold">{a.title}</h2>
                    <p className="text-sm text-gray-500">{new Date(a.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-blue-600">${a.current_price.toFixed(2)}</p>
                    <span className={`inline-block px-2 py-1 text-xs rounded ${
                      a.status === 'active' ? 'bg-green-100 text-green-800' : 
                      a.status === 'pending_approval' ? 'bg-yellow-100 text-yellow-800' : 
                      'bg-gray-100 text-gray-600'
                    }`}>{a.status}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}