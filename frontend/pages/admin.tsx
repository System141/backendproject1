import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';

interface User { id: string; name: string; email: string; role: string; status: string; }
interface Stats { total_users: number; total_auctions: number; total_bids: number; active_auctions: number; pending_auctions: number; total_revenue: number; total_commissions: number; }
interface SupportTicket { id: string; user_id: string; subject: string; message: string; status: string; created_at: string; }
interface PaymentItem { id: string; auction_id: string; buyer_id: string; amount: number; status: string; created_at: string; }
interface CommissionItem { id: string; auction_id: string; seller_id: string; amount: number; rate: number; status: string; created_at: string; }

export default function Admin() {
  const { t } = useTranslation();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<'users' | 'auctions' | 'stats' | 'tickets' | 'payments'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [allAuctions, setAllAuctions] = useState<any[]>([]);
  const [pendingAuctions, setPendingAuctions] = useState<any[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [filterRole, setFilterRole] = useState('');
  const [auctionFilterStatus, setAuctionFilterStatus] = useState('pending_approval');
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [payments, setPayments] = useState<PaymentItem[]>([]);
  const [commissions, setCommissions] = useState<CommissionItem[]>([]);

  useEffect(() => {
    if (!loading && (!user || user.role !== 'admin')) router.push('/');
  }, [user, loading, router]);

  const fetchData = () => {
    if (!user) return;
    const params = filterRole ? `?role=${filterRole}` : '';
    api.get<User[]>(`/api/admin/users${params}`).then(setUsers).catch(console.error);
    api.get<Stats>('/api/admin/stats').then(setStats).catch(console.error);
    api.get<any[]>('/api/admin/auctions?status=pending_approval').then(setPendingAuctions).catch(console.error);
  };

  const fetchAllAuctions = (status: string) => {
    if (!user) return;
    const params = status ? `?status=${status}` : '';
    api.get<any[]>(`/api/admin/auctions${params}`).then(setAllAuctions).catch(console.error);
  };

  const fetchTickets = () => {
    if (!user) return;
    api.get<SupportTicket[]>('/api/admin/support-tickets').then(setTickets).catch(console.error);
  };

  const fetchPayments = () => {
    if (!user) return;
    api.get<PaymentItem[]>('/api/payments').then(setPayments).catch(console.error);
    api.get<CommissionItem[]>('/api/payments/commissions').then(setCommissions).catch(console.error);
  };

  useEffect(() => { fetchData(); }, [user, filterRole]);

  useEffect(() => {
    if (tab === 'auctions') fetchAllAuctions(auctionFilterStatus);
    if (tab === 'tickets') fetchTickets();
    if (tab === 'payments') fetchPayments();
  }, [tab, user, auctionFilterStatus]);

  const updateStatus = async (userId: string, newStatus: string) => {
    await api.put(`/api/admin/users/${userId}/status?new_status=${newStatus}`, {});
    setUsers(prev => prev.map(u => u.id === userId ? { ...u, status: newStatus } : u));
  };

  const approveAuction = async (id: string) => {
    await api.post(`/api/auctions/${id}/approve`, {});
    setPendingAuctions(prev => prev.filter(a => a.id !== id));
    setAllAuctions(prev => prev.map(a => a.id === id ? { ...a, status: 'active' } : a));
  };

  const rejectAuction = async (id: string) => {
    await api.post(`/api/auctions/${id}/reject`, {});
    setPendingAuctions(prev => prev.filter(a => a.id !== id));
    setAllAuctions(prev => prev.map(a => a.id === id ? { ...a, status: 'cancelled' } : a));
  };

  const updateTicketStatus = async (ticketId: string, newStatus: string) => {
    await api.put(`/api/admin/support-tickets/${ticketId}`, { status: newStatus });
    setTickets(prev => prev.map(t => t.id === ticketId ? { ...t, status: newStatus } : t));
  };

  const updatePaymentStatus = async (paymentId: string, newStatus: string) => {
    await api.put(`/api/payments/${paymentId}/status?new_status=${newStatus}`, {});
    setPayments(prev => prev.map(p => p.id === paymentId ? { ...p, status: newStatus } : p));
  };

  if (loading || !user) return <Layout><p>{t('loading')}</p></Layout>;

  const statusColors: Record<string, string> = {
    active: 'bg-green-100 text-green-800',
    pending_approval: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-blue-100 text-blue-800',
    cancelled: 'bg-red-100 text-red-800',
    pending: 'bg-yellow-100 text-yellow-800',
    failed: 'bg-red-100 text-red-800',
    refunded: 'bg-gray-100 text-gray-600',
    open: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    resolved: 'bg-green-100 text-green-800',
    closed: 'bg-gray-100 text-gray-600',
  };

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-6">{t('nav_admin')}</h1>
      <div className="flex flex-wrap gap-2 mb-6">
        <button onClick={() => setTab('users')} className={`px-4 py-2 rounded text-sm ${tab === 'users' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>{t('admin_users')}</button>
        <button onClick={() => setTab('auctions')} className={`px-4 py-2 rounded text-sm ${tab === 'auctions' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>Auctions</button>
        <button onClick={() => setTab('tickets')} className={`px-4 py-2 rounded text-sm ${tab === 'tickets' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>Support Tickets</button>
        <button onClick={() => setTab('payments')} className={`px-4 py-2 rounded text-sm ${tab === 'payments' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>Payments</button>
        <button onClick={() => setTab('stats')} className={`px-4 py-2 rounded text-sm ${tab === 'stats' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>{t('admin_stats')}</button>
      </div>

      {tab === 'users' && (
        <div>
          <select className="mb-4 border rounded px-4 py-2" value={filterRole} onChange={e => setFilterRole(e.target.value)}>
            <option value="">All Roles</option>
            <option value="buyer">Buyer</option>
            <option value="seller">Seller</option>
            <option value="corporate_seller">Corporate Seller</option>
            <option value="admin">Admin</option>
          </select>
          <div className="bg-white rounded-lg shadow overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr><th className="p-3 text-left">Name</th><th className="p-3 text-left">Email</th><th className="p-3 text-left">Role</th><th className="p-3 text-left">Status</th><th className="p-3 text-left">Actions</th></tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} className="border-t">
                    <td className="p-3">{u.name}</td>
                    <td className="p-3">{u.email}</td>
                    <td className="p-3">{u.role}</td>
                    <td className="p-3"><span className={`px-2 py-1 rounded text-xs ${statusColors[u.status] || 'bg-gray-100'}`}>{u.status}</span></td>
                    <td className="p-3 space-x-2">
                      <button onClick={() => updateStatus(u.id, 'active')} className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded hover:bg-green-200">Active</button>
                      <button onClick={() => updateStatus(u.id, 'suspended')} className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded hover:bg-yellow-200">Suspend</button>
                      <button onClick={() => updateStatus(u.id, 'banned')} className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200">Ban</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'auctions' && (
        <div>
          <div className="flex gap-2 mb-4">
            <select className="border rounded px-4 py-2 text-sm" value={auctionFilterStatus} onChange={e => setAuctionFilterStatus(e.target.value)}>
              <option value="active">Active</option>
              <option value="pending_approval">Pending Approval</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="">All</option>
            </select>
          </div>
          <div className="bg-white rounded-lg shadow overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr><th className="p-3 text-left">Title</th><th className="p-3 text-left">Price</th><th className="p-3 text-left">Status</th><th className="p-3 text-left">Date</th><th className="p-3 text-left">Actions</th></tr>
              </thead>
              <tbody>
                {(auctionFilterStatus === 'pending_approval' ? pendingAuctions : allAuctions).map(a => (
                  <tr key={a.id} className="border-t">
                    <td className="p-3">
                      <a href={`/auctions/${a.id}`} className="text-blue-600 hover:underline" target="_blank" rel="noreferrer">{a.title}</a>
                    </td>
                    <td className="p-3">${a.current_price?.toFixed(2) || a.start_price?.toFixed(2)}</td>
                    <td className="p-3"><span className={`px-2 py-1 rounded text-xs ${statusColors[a.status] || 'bg-gray-100'}`}>{a.status}</span></td>
                    <td className="p-3">{new Date(a.created_at).toLocaleDateString()}</td>
                    <td className="p-3 space-x-2">
                      {a.status === 'pending_approval' && (
                        <>
                          <button onClick={() => approveAuction(a.id)} className="text-xs bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700">Approve</button>
                          <button onClick={() => rejectAuction(a.id)} className="text-xs bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700">Reject</button>
                        </>
                      )}
                      {a.status !== 'pending_approval' && <span className="text-xs text-gray-400">—</span>}
                    </td>
                  </tr>
                ))}
                {((auctionFilterStatus === 'pending_approval' ? pendingAuctions : allAuctions).length === 0) && (
                  <tr><td colSpan={5} className="p-6 text-center text-gray-500">No auctions found.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'tickets' && (
        <div className="bg-white rounded-lg shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr><th className="p-3 text-left">Subject</th><th className="p-3 text-left">Status</th><th className="p-3 text-left">Date</th><th className="p-3 text-left">Actions</th></tr>
            </thead>
            <tbody>
              {tickets.map(t => (
                <tr key={t.id} className="border-t">
                  <td className="p-3 max-w-xs truncate">{t.subject}</td>
                  <td className="p-3"><span className={`px-2 py-1 rounded text-xs ${statusColors[t.status] || 'bg-gray-100'}`}>{t.status}</span></td>
                  <td className="p-3">{new Date(t.created_at).toLocaleDateString()}</td>
                  <td className="p-3 space-x-2">
                    <button onClick={() => updateTicketStatus(t.id, 'open')} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded hover:bg-blue-200">Open</button>
                    <button onClick={() => updateTicketStatus(t.id, 'in_progress')} className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded hover:bg-yellow-200">In Progress</button>
                    <button onClick={() => updateTicketStatus(t.id, 'resolved')} className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded hover:bg-green-200">Resolved</button>
                    <button onClick={() => updateTicketStatus(t.id, 'closed')} className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded hover:bg-gray-200">Closed</button>
                  </td>
                </tr>
              ))}
              {tickets.length === 0 && (
                <tr><td colSpan={4} className="p-6 text-center text-gray-500">No support tickets.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'payments' && (
        <div className="space-y-6">
          <div>
            <h3 className="font-semibold mb-2">Payments</h3>
            <div className="bg-white rounded-lg shadow overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr><th className="p-3 text-left">Auction ID</th><th className="p-3 text-left">Amount</th><th className="p-3 text-left">Status</th><th className="p-3 text-left">Date</th><th className="p-3 text-left">Actions</th></tr>
                </thead>
                <tbody>
                  {payments.map(p => (
                    <tr key={p.id} className="border-t">
                      <td className="p-3 text-xs font-mono">{p.auction_id.slice(0, 8)}...</td>
                      <td className="p-3">${p.amount.toFixed(2)}</td>
                      <td className="p-3"><span className={`px-2 py-1 rounded text-xs ${statusColors[p.status] || 'bg-gray-100'}`}>{p.status}</span></td>
                      <td className="p-3">{new Date(p.created_at).toLocaleDateString()}</td>
                      <td className="p-3 space-x-2">
                        {p.status === 'pending' && (
                          <>
                            <button onClick={() => updatePaymentStatus(p.id, 'completed')} className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700">Complete</button>
                            <button onClick={() => updatePaymentStatus(p.id, 'failed')} className="text-xs bg-red-600 text-white px-2 py-1 rounded hover:bg-red-700">Fail</button>
                          </>
                        )}
                        {p.status === 'completed' && (
                          <button onClick={() => updatePaymentStatus(p.id, 'refunded')} className="text-xs bg-gray-600 text-white px-2 py-1 rounded hover:bg-gray-700">Refund</button>
                        )}
                        {p.status !== 'pending' && p.status !== 'completed' && <span className="text-xs text-gray-400">—</span>}
                      </td>
                    </tr>
                  ))}
                  {payments.length === 0 && (
                    <tr><td colSpan={5} className="p-6 text-center text-gray-500">No payments.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Commissions</h3>
            <div className="bg-white rounded-lg shadow overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr><th className="p-3 text-left">Auction ID</th><th className="p-3 text-left">Amount</th><th className="p-3 text-left">Rate</th><th className="p-3 text-left">Status</th><th className="p-3 text-left">Date</th></tr>
                </thead>
                <tbody>
                  {commissions.map(c => (
                    <tr key={c.id} className="border-t">
                      <td className="p-3 text-xs font-mono">{c.auction_id.slice(0, 8)}...</td>
                      <td className="p-3">${c.amount.toFixed(2)}</td>
                      <td className="p-3">{(c.rate * 100).toFixed(0)}%</td>
                      <td className="p-3"><span className={`px-2 py-1 rounded text-xs ${statusColors[c.status] || 'bg-gray-100'}`}>{c.status}</span></td>
                      <td className="p-3">{new Date(c.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                  {commissions.length === 0 && (
                    <tr><td colSpan={5} className="p-6 text-center text-gray-500">No commissions.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {tab === 'stats' && stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-3xl font-bold text-blue-600">{stats.total_users}</p><p className="text-gray-500">{t('admin_users')}</p></div>
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-3xl font-bold text-green-600">{stats.total_auctions}</p><p className="text-gray-500">{t('admin_auctions')}</p></div>
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-3xl font-bold text-purple-600">{stats.total_bids}</p><p className="text-gray-500">Bids</p></div>
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-2xl font-bold text-green-600">{stats.active_auctions}</p><p className="text-gray-500">Active</p></div>
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-2xl font-bold text-yellow-600">{stats.pending_auctions}</p><p className="text-gray-500">Pending</p></div>
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-2xl font-bold text-blue-600">${stats.total_revenue.toFixed(2)}</p><p className="text-gray-500">Revenue</p></div>
        </div>
      )}
    </Layout>
  );
}