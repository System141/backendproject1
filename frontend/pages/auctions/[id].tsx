import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuth } from '@/hooks/useAuth';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';

interface AuctionDetail {
  id: string; title: string; description: string; current_price: number; start_price: number;
  min_increment: number; end_time: string; status: string; seller_id: string;
  brand?: string; model?: string; year?: number; mileage?: number; images?: { image_url: string }[];
  category?: { name: string };
}

interface Bid { id: string; user_id: string; amount: number; created_at: string; }

export default function AuctionDetail() {
  const { t } = useTranslation();
  const router = useRouter();
  const { id } = router.query;
  const { user } = useAuth();
  const [auction, setAuction] = useState<AuctionDetail | null>(null);
  const [bids, setBids] = useState<Bid[]>([]);
  const [amount, setAmount] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    api.get<AuctionDetail>(`/api/auctions/${id}`).then(setAuction).catch(console.error);
    api.get<{bids: Bid[]}>(`/api/auctions/${id}/bids`).then(r => setBids(r.bids)).catch(console.error);
  }, [id]);

  useWebSocket(id as string, (msg) => {
    if (msg.type === 'new_bid') {
      setBids(prev => [msg.bid, ...prev]);
      setAuction(prev => prev ? { ...prev, current_price: msg.current_price, end_time: msg.end_time } : prev);
    }
  });

  const placeBid = async () => {
    if (!amount) return;
    try {
      await api.post(`/api/auctions/${id}/bids`, { amount: parseFloat(amount) });
      setAmount('');
      setError('');
    } catch (e: any) { setError(e.message); }
  };

  if (!auction) return <Layout><p>{t('loading')}</p></Layout>;

  return (
    <Layout>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <h1 className="text-3xl font-bold mb-4">{auction.title}</h1>
          {auction.category && <p className="text-gray-500 mb-2">{t('categories')}: {auction.category.name}</p>}
          {auction.brand && <p className="text-gray-700">{auction.brand} {auction.model} ({auction.year}) - {auction.mileage}km</p>}
          <p className="mt-4 whitespace-pre-wrap">{auction.description}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-3xl font-bold text-blue-600">${auction.current_price.toFixed(2)}</p>
          <p className="text-sm text-gray-500">{t('end_time')}: {new Date(auction.end_time).toLocaleString()}</p>
          {user && user.id !== auction.seller_id && auction.status === 'active' && (
            <div className="mt-4 space-y-2">
              <input className="w-full border rounded px-4 py-2" type="number" step="0.01" placeholder={t('bid_amount')} value={amount} onChange={e => setAmount(e.target.value)} />
              <button className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700" onClick={placeBid}>{t('place_bid')}</button>
              {error && <p className="text-red-500 text-sm">{error}</p>}
            </div>
          )}
          <div className="mt-6">
            <h3 className="font-semibold mb-2">{t('bid_history')} ({bids.length})</h3>
            {bids.length === 0 ? <p className="text-gray-500">{t('no_bids')}</p> : (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {bids.map(b => (
                  <div key={b.id} className="flex justify-between text-sm border-b pb-1">
                    <span className="font-medium">${b.amount.toFixed(2)}</span>
                    <span className="text-gray-500">{new Date(b.created_at).toLocaleTimeString()}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}