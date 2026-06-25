import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';

interface User { id: string; name: string; email: string; role: string; status: string; }
interface Stats { total_users: number; total_auctions: number; total_bids: number; active_auctions: number; pending_auctions: number; total_revenue: number; }

export default function Admin() {
  const { t } = useTranslation();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<'users' | 'auctions' | 'stats'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [auctions, setAuctions] = useState<any[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [filterRole, setFilterRole] = useState('');

  useEffect(() => {
    if (!loading && (!user || user.role !== 'admin')) router.push('/');
    if (user) {
      const params = filterRole ? `?role=${filterRole}` : '';
      api.get<User[]>(`/api/admin/users${params}`).then(setUsers).catch(console.error);
      api.get<Stats>('/api/admin/stats').then(setStats).catch(console.error);
      api.get<any[]>('/api/admin/auctions?status=pending_approval').then(setAuctions).catch(console.error);
    }
  }, [user, loading, filterRole, router]);

  const updateStatus = async (userId: string, newStatus: string) => {
    await api.put(`/api/admin/users/${userId}/status?new_status=${newStatus}`, {});
    setUsers(prev => prev.map(u => u.id === userId ? { ...u, status: newStatus } : u));
  };

  const approveAuction = async (id: string) => {
    await api.post(`/api/auctions/${id}/approve`, {});
    setAuctions(prev => prev.filter(a => a.id !== id));
  };

  const rejectAuction = async (id: string) => {
    await api.post(`/api/auctions/${id}/reject`, {});
    setAuctions(prev => prev.filter(a => a.id !== id));
  };

  if (loading || !user) return <Layout><p>{t('loading')}</p></Layout>;

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-6">{t('nav_admin')}</h1>
      <div className="flex gap-4 mb-6">
        <button onClick={() => setTab('users')} className={`px-4 py-2 rounded ${tab === 'users' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>{t('admin_users')}</button>
        <button onClick={() => setTab('auctions')} className={`px-4 py-2 rounded ${tab === 'auctions' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>Pending Auctions ({auctions.length})</button>
        <button onClick={() => setTab('stats')} className={`px-4 py-2 rounded ${tab === 'stats' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>{t('admin_stats')}</button>
      </div>

      {tab === 'users' && (
        <div>
          <select className="mb-4 border rounded px-4 py-2" value={filterRole} onChange={e => setFilterRole(e.target.value)}>
            <option value="">All Roles</option>
            <option value="buyer">Buyer</option>
            <option value="seller">Seller</option>
            <option value="admin">Admin</option>
          </select>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr><th className="p-3 text-left">Name</th><th className="p-3 text-left">Email</th><th className="p-3 text-left">Role</th><th className="p-3 text-left">{t('user_status')}</th><th className="p-3 text-left">Actions</th></tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} className="border-t">
                    <td className="p-3">{u.name}</td>
                    <td className="p-3">{u.email}</td>
                    <td className="p-3">{u.role}</td>
                    <td className="p-3">{u.status}</td>
                    <td className="p-3 space-x-2">
                      <button onClick={() => updateStatus(u.id, 'active')} className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">{t('active')}</button>
                      <button onClick={() => updateStatus(u.id, 'suspended')} className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">{t('suspended')}</button>
                      <button onClick={() => updateStatus(u.id, 'banned')} className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">{t('banned')}</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'auctions' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr><th className="p-3 text-left">Title</th><th className="p-3 text-left">Start Price</th><th className="p-3 text-left">Date</th><th className="p-3 text-left">Actions</th></tr>
            </thead>
            <tbody>
              {auctions.map(a => (
                <tr key={a.id} className="border-t">
                  <td className="p-3">
                    <a href={`/auctions/${a.id}`} className="text-blue-600 hover:underline" target="_blank">{a.title}</a>
                  </td>
                  <td className="p-3">${a.start_price}</td>
                  <td className="p-3">{new Date(a.created_at).toLocaleDateString()}</td>
                  <td className="p-3 space-x-2">
                    <button onClick={() => approveAuction(a.id)} className="text-xs bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700">Approve</button>
                    <button onClick={() => rejectAuction(a.id)} className="text-xs bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700">Reject</button>
                  </td>
                </tr>
              ))}
              {auctions.length === 0 && (
                <tr><td colSpan={4} className="p-6 text-center text-gray-500">No pending auctions.</td></tr>
              )}
            </tbody>
          </table>
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
