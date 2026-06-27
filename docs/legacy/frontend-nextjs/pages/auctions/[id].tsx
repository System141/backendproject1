import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuth } from '@/hooks/useAuth';
import Layout from '@/components/Layout';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';

interface AuctionDetail {
  id: string; title: string; description: string; current_price: number; start_price: number;
  min_increment: number; end_time: string; status: string; seller_id: string;
  brand?: string; model?: string; year?: number; mileage?: number;
  fuel_type?: string; transmission?: string; equipment_brand?: string;
  serial_number?: string; condition?: string; location?: string;
  images?: { id: string; image_url: string; sort_order: number }[];
  category?: { name: string; slug: string };
  winner_user_id?: string;
  seller_name?: string;
}

interface Bid { id: string; user_id: string; user_name?: string; amount: number; created_at: string; }

interface BidHistoryResponse {
  bids: Bid[];
  total_count: number;
  current_price?: number;
  auction_status?: string;
  min_increment?: number;
}

export default function AuctionDetail() {
  const { t } = useTranslation();
  const router = useRouter();
  const { id } = router.query;
  const { user } = useAuth();
  const [auction, setAuction] = useState<AuctionDetail | null>(null);
  const [bids, setBids] = useState<Bid[]>([]);
  const [amount, setAmount] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [onlineCount, setOnlineCount] = useState(1);
  const [timeLeft, setTimeLeft] = useState('');

  useEffect(() => {
    if (!id) return;
    api.get<AuctionDetail>(`/api/auctions/${id}`).then(setAuction).catch(console.error);
    api.get<BidHistoryResponse>(`/api/auctions/${id}/bids`).then(r => setBids(r.bids)).catch(console.error);
  }, [id]);

  // Countdown timer
  useEffect(() => {
    if (!auction?.end_time) return;
    const update = () => {
      const diff = new Date(auction.end_time).getTime() - Date.now();
      if (diff <= 0) { setTimeLeft('Ended'); return; }
      const d = Math.floor(diff / 86400000);
      const h = Math.floor((diff % 86400000) / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setTimeLeft(d > 0 ? `${d}d ${h}h ${m}m ${s}s` : `${h}h ${m}m ${s}s`);
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [auction?.end_time]);

  // WebSocket for live updates
  useWebSocket(id as string, (msg) => {
    if (msg.type === 'new_bid') {
      setBids(prev => [msg.bid, ...prev]);
      setAuction(prev => prev ? {
        ...prev,
        current_price: msg.current_price,
        end_time: msg.end_time || prev.end_time,
      } : prev);
    }
    if (msg.type === 'user_count') {
      setOnlineCount(msg.count);
    }
    if (msg.type === 'auction_status_changed') {
      setAuction(prev => prev ? { ...prev, status: msg.status, winner_user_id: msg.winner_user_id } : prev);
      // Refresh bid history when auction status changes
      if (id) api.get<BidHistoryResponse>(`/api/auctions/${id}/bids`).then(r => setBids(r.bids)).catch(console.error);
    }
    if (msg.type === 'ping') {
      // Respond to server ping
    }
  });

  const placeBid = async () => {
    if (!amount) return;
    setError('');
    setSuccess('');
    try {
      const res = await api.post<Bid>(`/api/auctions/${id}/bids`, { amount: parseFloat(amount) });
      setBids(prev => [res, ...prev]);
      setAuction(prev => prev ? { ...prev, current_price: parseFloat(amount) } : prev);
      setAmount('');
      setSuccess('Bid placed successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Failed to place bid');
    }
  };

  const handleFinalize = async () => {
    if (!confirm('Are you sure you want to finalize this auction?')) return;
    try {
      const res = await api.post<{status: string; winner_user_id: string | null; winning_bid: number | null}>(`/api/auctions/${id}/finalize`, {});
      setAuction(prev => prev ? { ...prev, status: 'completed', winner_user_id: res.winner_user_id || undefined } : prev);
      setSuccess('Auction finalized successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Failed to finalize auction');
    }
  };

  if (!auction) return <Layout><p>{t('loading')}</p></Layout>;

  const currentPrice = auction.current_price ?? auction.start_price ?? 0;
  const minBid = currentPrice + (auction.min_increment ?? 0);
  const isSellerOrAdmin = user && (user.id === auction.seller_id || user.role === 'admin');
  const auctionEnded = timeLeft === 'Ended' || new Date(auction.end_time).getTime() < Date.now();

  return (
    <Layout>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <h1 className="text-3xl font-bold mb-4">{auction.title}</h1>
          {auction.category && (
            <p className="text-gray-500 mb-2">
              {t('categories')}: <span className="font-medium">{auction.category.name}</span>
            </p>
          )}

          {/* Vehicle details */}
          {auction.brand && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4 p-4 bg-gray-50 rounded-lg">
              <div><span className="text-xs text-gray-500">{t('detail_brand')}</span><p className="font-medium">{auction.brand}</p></div>
              <div><span className="text-xs text-gray-500">{t('detail_model')}</span><p className="font-medium">{auction.model}</p></div>
              <div><span className="text-xs text-gray-500">{t('detail_year')}</span><p className="font-medium">{auction.year}</p></div>
              <div><span className="text-xs text-gray-500">{t('detail_mileage')}</span><p className="font-medium">{auction.mileage?.toLocaleString()} km</p></div>
              <div><span className="text-xs text-gray-500">{t('detail_fuel')}</span><p className="font-medium">{auction.fuel_type}</p></div>
              <div><span className="text-xs text-gray-500">{t('detail_trans')}</span><p className="font-medium">{auction.transmission}</p></div>
            </div>
          )}

          {/* Equipment details */}
          {auction.equipment_brand && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4 p-4 bg-gray-50 rounded-lg">
              <div><span className="text-xs text-gray-500">{t('detail_ebrand')}</span><p className="font-medium">{auction.equipment_brand}</p></div>
              <div><span className="text-xs text-gray-500">{t('detail_serial')}</span><p className="font-medium">{auction.serial_number}</p></div>
              <div><span className="text-xs text-gray-500">{t('detail_cond')}</span><p className="font-medium">{auction.condition}</p></div>
              <div><span className="text-xs text-gray-500">{t('detail_loc')}</span><p className="font-medium">{auction.location}</p></div>
            </div>
          )}

          <p className="mt-4 whitespace-pre-wrap text-gray-700">{auction.description}</p>

          {/* Images */}
          {auction.images && auction.images.length > 0 && (
            <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-4">
              {auction.images.sort((a, b) => a.sort_order - b.sort_order).map(img => (
                <img key={img.id} src={img.image_url} alt={auction.title} className="rounded-lg object-cover w-full h-48" />
              ))}
            </div>
          )}
        </div>

        {/* Sidebar: Bidding */}
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          {/* Online count badge */}
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span className={`w-2 h-2 rounded-full ${onlineCount > 0 ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
            {onlineCount > 0 ? `${onlineCount} watching` : 'Offline'}
          </div>

          <p className="text-3xl font-bold text-blue-600">€{currentPrice.toFixed(2)}</p>
          <p className="text-sm text-gray-500">{t('detail_cur')}</p>

          {/* Status badge */}
          <span className={`inline-block px-3 py-1 rounded text-sm font-medium ${
            auction.status === 'active' ? 'bg-green-100 text-green-800' :
            auction.status === 'completed' ? 'bg-blue-100 text-blue-800' :
            auction.status === 'pending_approval' ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            {t('detail_st')}: {auction.status.replace('_', ' ')}
          </span>

          {/* Countdown */}
          <div className="text-sm">
            <span className="text-gray-500">{t('detail_time')}:</span>
            <span className={`ml-2 font-mono font-bold ${timeLeft === 'Ended' ? 'text-red-600' : 'text-gray-900'}`}>{timeLeft}</span>
          </div>

          <p className="text-sm text-gray-500">{t('detail_bcount')}: {bids.length}</p>

          {/* Bid form */}
          {user && user.id !== auction.seller_id && auction.status === 'active' && (
            <div className="space-y-3">
              <div>
                <input
                  className="w-full border rounded px-4 py-2 text-lg"
                  type="number"
                  step={(auction.min_increment || 1).toString()}
                  min={minBid}
                  placeholder={`€${minBid.toFixed(2)}`}
                  value={amount}
                  onChange={e => setAmount(e.target.value)}
                />
                <p className="text-xs text-gray-400 mt-1">{t('detail_n')}</p>
              </div>
              <button
                className="w-full bg-blue-600 text-white py-2 rounded-lg text-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                onClick={placeBid}
                disabled={!amount || parseFloat(amount) < minBid}
              >
                {t('detail_btn')}
              </button>
              {error && <p className="text-red-500 text-sm bg-red-50 p-2 rounded">{error}</p>}
              {success && <p className="text-green-600 text-sm bg-green-50 p-2 rounded">{success}</p>}
            </div>
          )}

          {!user && auction.status === 'active' && (
            <p className="text-sm text-gray-500 text-center">
              <Link href="/login" className="text-blue-600 hover:underline">Login</Link> to place a bid
            </p>
          )}

          {/* Finalize button for seller/admin when auction has ended */}
          {isSellerOrAdmin && auction.status === 'active' && auctionEnded && (
            <button
              className="w-full bg-purple-600 text-white py-2 rounded-lg text-lg font-semibold hover:bg-purple-700 transition-colors"
              onClick={handleFinalize}
            >
              Finalize Auction
            </button>
          )}

          {auction.status === 'completed' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
              <p className="text-green-800 font-semibold">Auction completed</p>
              {auction.winner_user_id ? (
                <>
                  {user?.id === auction.winner_user_id ? (
                    <p className="text-green-600 text-sm mt-1">You won this auction!</p>
                  ) : (
                    <p className="text-gray-600 text-sm mt-1">Winner: {auction.winner_user_id}</p>
                  )}
                </>
              ) : (
                <p className="text-gray-500 text-sm mt-1">No winning bids</p>
              )}
            </div>
          )}

          {/* Bid History */}
          <div className="mt-6">
            <h3 className="font-semibold mb-2">{t('detail_hist')} ({bids.length})</h3>
            {bids.length === 0 ? (
              <p className="text-gray-500 text-sm">{t('no_bids')}</p>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {bids.map((b, i) => (
                  <div key={b.id} className={`flex justify-between text-sm py-2 px-2 rounded ${i === 0 ? 'bg-yellow-50 border border-yellow-200' : 'border-b'}`}>
                    <div>
                      <span className="font-bold">€{b.amount.toFixed(2)}</span>
                      {b.user_name && <span className="text-gray-400 ml-2 text-xs">{b.user_name}</span>}
                    </div>
                    <span className="text-gray-400 text-xs">{new Date(b.created_at).toLocaleTimeString()}</span>
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