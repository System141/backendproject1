import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import Layout from '@/components/Layout';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';

interface Bid {
  id: string;
  auction_id: string;
  user_id: string;
  amount: number;
  created_at: string;
  user_name?: string;
  auction_title?: string;
}

export default function MyBids() {
  const { t } = useTranslation();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [bids, setBids] = useState<Bid[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
      return;
    }
    if (user) {
      api.get<Bid[]>('/api/auctions/bids/my')
        .then(setBids)
        .catch(() => {})
        .finally(() => setIsLoading(false));
    }
  }, [user, loading, router]);

  if (loading || !user) return <Layout><p className="p-6">{t('loading')}</p></Layout>;

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">{t('my_bids') || 'My Bids'}</h1>

        {isLoading ? (
          <p className="text-gray-500">{t('loading')}</p>
        ) : bids.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-500 mb-4">{t('no_bids') || 'No bids placed yet.'}</p>
            <Link
              href="/auctions"
              className="text-blue-600 hover:underline font-medium"
            >
              Browse auctions
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {bids.map(b => (
              <Link key={b.id} href={`/auctions/${b.auction_id}`} className="block bg-white rounded-lg shadow p-4 hover:shadow-md transition">
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="font-semibold">{b.auction_title || b.auction_id}</h2>
                    <p className="text-sm text-gray-500">{t('your_bid') || 'Your bid'}: €{b.amount.toFixed(2)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-400">{new Date(b.created_at).toLocaleDateString()}</p>
                    <p className="text-xs text-gray-400">{new Date(b.created_at).toLocaleTimeString()}</p>
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