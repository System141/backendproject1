import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';

interface User { id: string; name: string; email: string; role: string; status: string; }
interface Stats { total_users: number; total_auctions: number; total_bids: number; active_auctions: number; completed_auctions: number; pending_auctions: number; total_revenue: number; total_commissions: number; }
interface SupportTicket { id: string; user_id: string; subject: string; message: string; status: string; created_at: string; }
interface PaymentItem { id: string; auction_id: string; buyer_id: string; amount: number; status: string; created_at: string; }
interface CommissionItem { id: string; auction_id: string; seller_id: string; amount: number; rate: number; status: string; created_at: string; }
interface BidItem { id: string; auction_id: string; user_id: string; amount: number; created_at: string; }
interface AuditLogItem { id: string; user_id: string; action: string; entity_type: string; entity_id: string; details: string; created_at: string; }
interface Category { id: number; name: string; slug: string; parent_id: number | null; status: string; }

type Tab = 'users' | 'auctions' | 'stats' | 'tickets' | 'payments' | 'categories' | 'bids' | 'audit';

export default function Admin() {
  const { t } = useTranslation();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>('stats');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{ message: string; onConfirm: () => void } | null>(null);
  const [ticketDetail, setTicketDetail] = useState<SupportTicket | null>(null);

  // Users state
  const [users, setUsers] = useState<User[]>([]);
  const [filterRole, setFilterRole] = useState('');

  // Auctions state
  const [allAuctions, setAllAuctions] = useState<any[]>([]);
  const [pendingAuctions, setPendingAuctions] = useState<any[]>([]);
  const [auctionFilterStatus, setAuctionFilterStatus] = useState('pending_approval');
  const [auctionFilterFeatured, setAuctionFilterFeatured] = useState('');

  // Stats state
  const [stats, setStats] = useState<Stats | null>(null);

  // Tickets state
  const [tickets, setTickets] = useState<SupportTicket[]>([]);

  // Payments state
  const [payments, setPayments] = useState<PaymentItem[]>([]);
  const [commissions, setCommissions] = useState<CommissionItem[]>([]);

  // Bids state
  const [bids, setBids] = useState<BidItem[]>([]);
  const [bidFilterAuction, setBidFilterAuction] = useState('');

  // Categories state
  const [categories, setCategories] = useState<Category[]>([]);
  const [editCategory, setEditCategory] = useState<Category | null>(null);
  const [newCategory, setNewCategory] = useState({ name: '', slug: '', parent_id: '' });

  // Audit logs state
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [auditFilterAction, setAuditFilterAction] = useState('');

  // Loading states
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [loadingAuctions, setLoadingAuctions] = useState(false);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [loadingPayments, setLoadingPayments] = useState(false);
  const [loadingBids, setLoadingBids] = useState(false);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [loadingAudit, setLoadingAudit] = useState(false);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleError = (err: any, defaultMsg: string) => {
    const msg = err?.message || err?.statusText || defaultMsg;
    showToast(msg, 'error');
  };

  useEffect(() => {
    if (!loading && (!user || user.role !== 'admin')) router.push('/');
  }, [user, loading, router]);

  // ---- Fetch functions ----
  const fetchUsers = useCallback(() => {
    if (!user) return;
    setLoadingUsers(true);
    const params = filterRole ? `?role=${filterRole}` : '';
    api.get<User[]>(`/api/admin/users${params}`)
      .then(setUsers)
      .catch(e => showToast(e?.message || 'Failed to load users', 'error'))
      .finally(() => setLoadingUsers(false));
  }, [user, filterRole]);

  const fetchStats = useCallback(() => {
    if (!user) return;
    api.get<Stats>('/api/admin/stats')
      .then(setStats)
      .catch(e => showToast(e?.message || 'Failed to load stats', 'error'));
  }, [user]);

  const fetchPendingAuctions = useCallback(() => {
    if (!user) return;
    api.get<any[]>('/api/admin/auctions?status=pending_approval')
      .then(setPendingAuctions)
      .catch(e => showToast(e?.message || 'Failed to load pending auctions', 'error'));
  }, [user]);

  const fetchAllAuctions = useCallback((status: string, featured: string) => {
    if (!user) return;
    setLoadingAuctions(true);
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (featured) params.set('featured', featured);
    const qs = params.toString();
    api.get<any[]>(`/api/admin/auctions${qs ? `?${qs}` : ''}`)
      .then(setAllAuctions)
      .catch(e => showToast(e?.message || 'Failed to load auctions', 'error'))
      .finally(() => setLoadingAuctions(false));
  }, [user]);

  const fetchTickets = useCallback(() => {
    if (!user) return;
    setLoadingTickets(true);
    api.get<SupportTicket[]>('/api/admin/support-tickets')
      .then(setTickets)
      .catch(e => showToast(e?.message || 'Failed to load tickets', 'error'))
      .finally(() => setLoadingTickets(false));
  }, [user]);

  const fetchPayments = useCallback(() => {
    if (!user) return;
    setLoadingPayments(true);
    Promise.all([
      api.get<PaymentItem[]>('/api/payments'),
      api.get<CommissionItem[]>('/api/payments/commissions'),
    ])
      .then(([p, c]) => {
        setPayments(p);
        setCommissions(c);
      })
      .catch(e => showToast(e?.message || 'Failed to load payments', 'error'))
      .finally(() => setLoadingPayments(false));
  }, [user]);

  const fetchBids = useCallback(() => {
    if (!user) return;
    setLoadingBids(true);
    const params = bidFilterAuction ? `?auction_id=${bidFilterAuction}` : '';
    api.get<BidItem[]>(`/api/admin/bids${params}`)
      .then(setBids)
      .catch(e => showToast(e?.message || 'Failed to load bids', 'error'))
      .finally(() => setLoadingBids(false));
  }, [user, bidFilterAuction]);

  const fetchCategories = useCallback(() => {
    if (!user) return;
    setLoadingCategories(true);
    api.get<Category[]>('/api/admin/categories')
      .then(setCategories)
      .catch(e => showToast(e?.message || 'Failed to load categories', 'error'))
      .finally(() => setLoadingCategories(false));
  }, [user]);

  const fetchAuditLogs = useCallback(() => {
    if (!user) return;
    setLoadingAudit(true);
    const params = auditFilterAction ? `?action=${auditFilterAction}` : '';
    api.get<AuditLogItem[]>(`/api/admin/audit-logs${params}`)
      .then(setAuditLogs)
      .catch(e => showToast(e?.message || 'Failed to load audit logs', 'error'))
      .finally(() => setLoadingAudit(false));
  }, [user, auditFilterAction]);

  // ---- Effects ----
  useEffect(() => { fetchUsers(); fetchStats(); fetchPendingAuctions(); }, [user, fetchUsers, fetchStats, fetchPendingAuctions]);

  useEffect(() => {
    if (tab === 'auctions') fetchAllAuctions(auctionFilterStatus, auctionFilterFeatured);
    if (tab === 'tickets') fetchTickets();
    if (tab === 'payments') fetchPayments();
    if (tab === 'bids') fetchBids();
    if (tab === 'categories') fetchCategories();
    if (tab === 'audit') fetchAuditLogs();
  }, [tab, user, auctionFilterStatus, fetchAllAuctions, fetchTickets, fetchPayments, fetchBids, fetchCategories, fetchAuditLogs]);

  // ---- Actions ----
  const updateUserStatus = async (userId: string, newStatus: string) => {
    try {
      await api.put(`/api/admin/users/${userId}/status?new_status=${newStatus}`, {});
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, status: newStatus } : u));
      showToast(`User status updated to ${newStatus}`);
    } catch (e) { handleError(e, 'Failed to update user status'); }
  };

  const approveAuction = async (id: string) => {
    try {
      await api.post(`/api/auctions/${id}/approve`, {});
      setPendingAuctions(prev => prev.filter(a => a.id !== id));
      setAllAuctions(prev => prev.map(a => a.id === id ? { ...a, status: 'active' } : a));
      showToast('Auction approved');
    } catch (e) { handleError(e, 'Failed to approve auction'); }
  };

  const rejectAuction = async (id: string) => {
    try {
      await api.post(`/api/auctions/${id}/reject`, {});
      setPendingAuctions(prev => prev.filter(a => a.id !== id));
      setAllAuctions(prev => prev.map(a => a.id === id ? { ...a, status: 'cancelled' } : a));
      showToast('Auction rejected');
    } catch (e) { handleError(e, 'Failed to reject auction'); }
  };

  const toggleFeatured = async (id: string, current: boolean) => {
    try {
      await api.put(`/api/admin/auctions/${id}/featured?is_featured=${!current}`, {});
      setAllAuctions(prev => prev.map(a => a.id === id ? { ...a, is_featured: !current } : a));
      showToast(`Featured ${!current ? 'enabled' : 'disabled'}`);
    } catch (e) { handleError(e, 'Failed to toggle featured'); }
  };

  const updateTicketStatus = async (ticketId: string, newStatus: string) => {
    try {
      await api.put(`/api/admin/support-tickets/${ticketId}`, { status: newStatus });
      setTickets(prev => prev.map(t => t.id === ticketId ? { ...t, status: newStatus } : t));
      showToast(`Ticket status updated to ${newStatus}`);
    } catch (e) { handleError(e, 'Failed to update ticket status'); }
  };

  const updatePaymentStatus = async (paymentId: string, newStatus: string) => {
    try {
      await api.put(`/api/payments/${paymentId}/status?new_status=${newStatus}`, {});
      setPayments(prev => prev.map(p => p.id === paymentId ? { ...p, status: newStatus } : p));
      showToast(`Payment status updated to ${newStatus}`);
    } catch (e) { handleError(e, 'Failed to update payment status'); }
  };

  const updateCommissionStatus = async (commissionId: string, newStatus: string) => {
    try {
      await api.put(`/api/admin/commissions/${commissionId}/status?new_status=${newStatus}`, {});
      setCommissions(prev => prev.map(c => c.id === commissionId ? { ...c, status: newStatus } : c));
      showToast(`Commission status updated to ${newStatus}`);
    } catch (e) { handleError(e, 'Failed to update commission status'); }
  };

  const handleCreateCategory = async () => {
    if (!newCategory.name || !newCategory.slug) {
      showToast('Name and slug are required', 'error');
      return;
    }
    try {
      await api.post('/api/admin/categories', {
        name: newCategory.name,
        slug: newCategory.slug,
        parent_id: newCategory.parent_id ? parseInt(newCategory.parent_id) : null,
      });
      setNewCategory({ name: '', slug: '', parent_id: '' });
      showToast('Category created');
      fetchCategories();
    } catch (e) { handleError(e, 'Failed to create category'); }
  };

  const handleUpdateCategory = async () => {
    if (!editCategory) return;
    try {
      await api.put(`/api/admin/categories/${editCategory.id}`, {
        name: editCategory.name,
        slug: editCategory.slug,
        status: editCategory.status,
      });
      setEditCategory(null);
      showToast('Category updated');
      fetchCategories();
    } catch (e) { handleError(e, 'Failed to update category'); }
  };

  const handleDeleteCategory = async (id: number) => {
    try {
      await api.del(`/api/admin/categories/${id}`);
      showToast('Category deactivated');
      fetchCategories();
    } catch (e) { handleError(e, 'Failed to delete category'); }
  };

  if (loading || !user) return <Layout><p className="p-6">{t('loading')}</p></Layout>;

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

  const tabs: { key: Tab; label: string }[] = [
    { key: 'stats', label: t('admin_stats') },
    { key: 'users', label: t('admin_users') },
    { key: 'auctions', label: t('admin_auctions') },
    { key: 'categories', label: 'Categories' },
    { key: 'bids', label: 'Bids' },
    { key: 'tickets', label: 'Support Tickets' },
    { key: 'payments', label: 'Payments' },
    { key: 'audit', label: 'Audit Log' },
  ];

  return (
    <Layout>
      {/* Toast notification */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-lg shadow-lg text-white text-sm ${toast.type === 'error' ? 'bg-red-600' : 'bg-green-600'}`}>
          {toast.message}
        </div>
      )}

      {/* Confirm dialog */}
      {confirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-30 z-40 flex items-center justify-center" onClick={() => setConfirmDialog(null)}>
          <div className="bg-white rounded-lg p-6 max-w-sm mx-4 shadow-xl" onClick={e => e.stopPropagation()}>
            <p className="mb-4">{confirmDialog.message}</p>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setConfirmDialog(null)} className="px-4 py-2 text-sm bg-gray-200 rounded hover:bg-gray-300">Cancel</button>
              <button onClick={() => { confirmDialog.onConfirm(); setConfirmDialog(null); }} className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">Confirm</button>
            </div>
          </div>
        </div>
      )}

      {/* Ticket detail modal */}
      {ticketDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-30 z-40 flex items-center justify-center" onClick={() => setTicketDetail(null)}>
          <div className="bg-white rounded-lg p-6 max-w-lg mx-4 shadow-xl w-full" onClick={e => e.stopPropagation()}>
            <h3 className="font-bold text-lg mb-2">{ticketDetail.subject}</h3>
            <p className="text-sm text-gray-500 mb-1">From user: {ticketDetail.user_id}</p>
            <p className="text-xs text-gray-400 mb-3">{new Date(ticketDetail.created_at).toLocaleString()}</p>
            <div className="bg-gray-50 rounded p-3 text-sm whitespace-pre-wrap mb-4">{ticketDetail.message}</div>
            <div className="flex gap-2">
              <span className={`px-2 py-1 rounded text-xs ${statusColors[ticketDetail.status] || 'bg-gray-100'}`}>{ticketDetail.status}</span>
              <button onClick={() => setTicketDetail(null)} className="ml-auto px-4 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300">Close</button>
            </div>
          </div>
        </div>
      )}

      <h1 className="text-2xl font-bold mb-6">{t('nav_admin')}</h1>

      {/* Tab buttons */}
      <div className="flex flex-wrap gap-2 mb-6">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded text-sm ${tab === t.key ? 'bg-blue-600 text-white' : 'bg-gray-200 hover:bg-gray-300'}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ==================== STATS ==================== */}
      {tab === 'stats' && stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-3xl font-bold text-blue-600">{stats.total_users}</p><p className="text-gray-500">{t('admin_users')}</p></div>
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-3xl font-bold text-green-600">{stats.total_auctions}</p><p className="text-gray-500">{t('admin_auctions')}</p></div>
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-3xl font-bold text-purple-600">{stats.total_bids}</p><p className="text-gray-500">Bids</p></div>
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-2xl font-bold text-green-600">{stats.active_auctions}</p><p className="text-gray-500">Active</p></div>
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-2xl font-bold text-yellow-600">{stats.pending_auctions}</p><p className="text-gray-500">Pending</p></div>
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-2xl font-bold text-indigo-600">{stats.completed_auctions}</p><p className="text-gray-500">Completed</p></div>
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-2xl font-bold text-blue-600">${stats.total_revenue.toFixed(2)}</p><p className="text-gray-500">Revenue</p></div>
          <div className="bg-white rounded-lg shadow p-6 text-center"><p className="text-2xl font-bold text-teal-600">${stats.total_commissions.toFixed(2)}</p><p className="text-gray-500">Commissions</p></div>
        </div>
      )}

      {/* ==================== USERS ==================== */}
      {tab === 'users' && (
        <div>
          <select className="mb-4 border rounded px-4 py-2" value={filterRole} onChange={e => setFilterRole(e.target.value)}>
            <option value="">All Roles</option>
            <option value="buyer">Buyer</option>
            <option value="seller">Seller</option>
            <option value="corporate_seller">Corporate Seller</option>
            <option value="admin">Admin</option>
          </select>
          {loadingUsers ? (
            <p className="text-gray-500">{t('loading')}</p>
          ) : users.length === 0 ? (
            <p className="text-gray-500 py-4">No users found.</p>
          ) : (
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
                        <button onClick={() => setConfirmDialog({ message: `Activate user ${u.name}?`, onConfirm: () => updateUserStatus(u.id, 'active') })} className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded hover:bg-green-200">Active</button>
                        <button onClick={() => setConfirmDialog({ message: `Suspend user ${u.name}?`, onConfirm: () => updateUserStatus(u.id, 'suspended') })} className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded hover:bg-yellow-200">Suspend</button>
                        <button onClick={() => setConfirmDialog({ message: `Ban user ${u.name}?`, onConfirm: () => updateUserStatus(u.id, 'banned') })} className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200">Ban</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ==================== AUCTIONS ==================== */}
      {tab === 'auctions' && (
        <div>
          <div className="flex gap-2 mb-4 flex-wrap">
            <select className="border rounded px-4 py-2 text-sm" value={auctionFilterStatus} onChange={e => setAuctionFilterStatus(e.target.value)}>
              <option value="active">Active</option>
              <option value="pending_approval">Pending Approval</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="">All</option>
            </select>
            <select className="border rounded px-4 py-2 text-sm" value={auctionFilterFeatured} onChange={e => setAuctionFilterFeatured(e.target.value)}>
              <option value="">All Auctions</option>
              <option value="true">Featured Only</option>
              <option value="false">Non-Featured</option>
            </select>
          </div>
          {loadingAuctions ? (
            <p className="text-gray-500">{t('loading')}</p>
          ) : (auctionFilterStatus === 'pending_approval' ? pendingAuctions : allAuctions).length === 0 ? (
            <p className="text-gray-500 py-4">No auctions found.</p>
          ) : (
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
                        {a.is_featured && <span className="ml-1 text-yellow-500">★</span>}
                      </td>
                      <td className="p-3">${a.current_price?.toFixed(2) || a.start_price?.toFixed(2)}</td>
                      <td className="p-3"><span className={`px-2 py-1 rounded text-xs ${statusColors[a.status] || 'bg-gray-100'}`}>{a.status}</span></td>
                      <td className="p-3">{new Date(a.created_at).toLocaleDateString()}</td>
                      <td className="p-3 space-x-2 whitespace-nowrap">
                        {a.status === 'pending_approval' && (
                          <>
                            <button onClick={() => setConfirmDialog({ message: `Approve auction "${a.title}"?`, onConfirm: () => approveAuction(a.id) })} className="text-xs bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700">Approve</button>
                            <button onClick={() => setConfirmDialog({ message: `Reject auction "${a.title}"?`, onConfirm: () => rejectAuction(a.id) })} className="text-xs bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700">Reject</button>
                          </>
                        )}
                        {a.status !== 'pending_approval' && <span className="text-xs text-gray-400">—</span>}
                        <button
                          onClick={() => toggleFeatured(a.id, a.is_featured)}
                          className={`text-xs px-2 py-1 rounded ${a.is_featured ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                        >
                          {a.is_featured ? 'Unfeature' : 'Feature'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ==================== CATEGORIES ==================== */}
      {tab === 'categories' && (
        <div>
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <h3 className="font-semibold mb-3">{editCategory ? 'Edit Category' : 'Create Category'}</h3>
            <div className="flex flex-wrap gap-2 items-end">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Name</label>
                <input
                  className="border rounded px-3 py-2 text-sm"
                  value={editCategory ? editCategory.name : newCategory.name}
                  onChange={e => editCategory ? setEditCategory({ ...editCategory, name: e.target.value }) : setNewCategory({ ...newCategory, name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Slug</label>
                <input
                  className="border rounded px-3 py-2 text-sm"
                  value={editCategory ? editCategory.slug : newCategory.slug}
                  onChange={e => editCategory ? setEditCategory({ ...editCategory, slug: e.target.value }) : setNewCategory({ ...newCategory, slug: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Parent ID (optional)</label>
                <input
                  className="border rounded px-3 py-2 text-sm"
                  type="number"
                  value={editCategory ? editCategory.parent_id?.toString() || '' : newCategory.parent_id}
                  onChange={e => editCategory ? setEditCategory({ ...editCategory, parent_id: e.target.value ? parseInt(e.target.value) : null }) : setNewCategory({ ...newCategory, parent_id: e.target.value })}
                />
              </div>
              <button
                onClick={editCategory ? handleUpdateCategory : handleCreateCategory}
                className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                {editCategory ? 'Update' : 'Create'}
              </button>
              {editCategory && (
                <button onClick={() => setEditCategory(null)} className="px-4 py-2 bg-gray-200 rounded text-sm hover:bg-gray-300">Cancel</button>
              )}
            </div>
          </div>

          {loadingCategories ? (
            <p className="text-gray-500">{t('loading')}</p>
          ) : categories.length === 0 ? (
            <p className="text-gray-500 py-4">No categories.</p>
          ) : (
            <div className="bg-white rounded-lg shadow overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr><th className="p-3 text-left">ID</th><th className="p-3 text-left">Name</th><th className="p-3 text-left">Slug</th><th className="p-3 text-left">Parent</th><th className="p-3 text-left">Status</th><th className="p-3 text-left">Actions</th></tr>
                </thead>
                <tbody>
                  {categories.map(c => (
                    <tr key={c.id} className="border-t">
                      <td className="p-3">{c.id}</td>
                      <td className="p-3">{c.name}</td>
                      <td className="p-3 text-xs font-mono">{c.slug}</td>
                      <td className="p-3">{c.parent_id ?? '—'}</td>
                      <td className="p-3"><span className={`px-2 py-1 rounded text-xs ${statusColors[c.status] || 'bg-gray-100'}`}>{c.status}</span></td>
                      <td className="p-3 space-x-2">
                        <button onClick={() => setEditCategory(c)} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded hover:bg-blue-200">Edit</button>
                        <button onClick={() => setConfirmDialog({ message: `Deactivate category "${c.name}"?`, onConfirm: () => handleDeleteCategory(c.id) })} className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200">Deactivate</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ==================== BIDS ==================== */}
      {tab === 'bids' && (
        <div>
          <div className="flex gap-2 mb-4">
            <input
              className="border rounded px-4 py-2 text-sm flex-1 max-w-xs"
              placeholder="Filter by auction ID"
              value={bidFilterAuction}
              onChange={e => setBidFilterAuction(e.target.value)}
            />
          </div>
          {loadingBids ? (
            <p className="text-gray-500">{t('loading')}</p>
          ) : bids.length === 0 ? (
            <p className="text-gray-500 py-4">No bids found.</p>
          ) : (
            <div className="bg-white rounded-lg shadow overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr><th className="p-3 text-left">Auction</th><th className="p-3 text-left">User</th><th className="p-3 text-left">Amount</th><th className="p-3 text-left">Date</th></tr>
                </thead>
                <tbody>
                  {bids.map(b => (
                    <tr key={b.id} className="border-t">
                      <td className="p-3 text-xs font-mono">{b.auction_id.slice(0, 8)}...</td>
                      <td className="p-3 text-xs font-mono">{b.user_id.slice(0, 8)}...</td>
                      <td className="p-3">${b.amount.toFixed(2)}</td>
                      <td className="p-3">{new Date(b.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ==================== SUPPORT TICKETS ==================== */}
      {tab === 'tickets' && (
        <div>
          {loadingTickets ? (
            <p className="text-gray-500">{t('loading')}</p>
          ) : tickets.length === 0 ? (
            <p className="text-gray-500 py-4">No support tickets.</p>
          ) : (
            <div className="bg-white rounded-lg shadow overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr><th className="p-3 text-left">Subject</th><th className="p-3 text-left">Status</th><th className="p-3 text-left">Date</th><th className="p-3 text-left">Actions</th></tr>
                </thead>
                <tbody>
                  {tickets.map(t => (
                    <tr key={t.id} className="border-t">
                      <td className="p-3 max-w-xs truncate">
                        <button onClick={() => setTicketDetail(t)} className="text-blue-600 hover:underline text-left">{t.subject}</button>
                      </td>
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
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ==================== PAYMENTS ==================== */}
      {tab === 'payments' && (
        <div className="space-y-6">
          <div>
            <h3 className="font-semibold mb-2">Payments</h3>
            {loadingPayments ? (
              <p className="text-gray-500">{t('loading')}</p>
            ) : payments.length === 0 ? (
              <p className="text-gray-500 py-4">No payments.</p>
            ) : (
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
                              <button onClick={() => setConfirmDialog({ message: 'Complete this payment?', onConfirm: () => updatePaymentStatus(p.id, 'completed') })} className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700">Complete</button>
                              <button onClick={() => setConfirmDialog({ message: 'Fail this payment?', onConfirm: () => updatePaymentStatus(p.id, 'failed') })} className="text-xs bg-red-600 text-white px-2 py-1 rounded hover:bg-red-700">Fail</button>
                            </>
                          )}
                          {p.status === 'completed' && (
                            <button onClick={() => setConfirmDialog({ message: 'Refund this payment?', onConfirm: () => updatePaymentStatus(p.id, 'refunded') })} className="text-xs bg-gray-600 text-white px-2 py-1 rounded hover:bg-gray-700">Refund</button>
                          )}
                          {p.status !== 'pending' && p.status !== 'completed' && <span className="text-xs text-gray-400">—</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          <div>
            <h3 className="font-semibold mb-2">Commissions</h3>
            {loadingPayments ? (
              <p className="text-gray-500">{t('loading')}</p>
            ) : commissions.length === 0 ? (
              <p className="text-gray-500 py-4">No commissions.</p>
            ) : (
              <div className="bg-white rounded-lg shadow overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr><th className="p-3 text-left">Auction ID</th><th className="p-3 text-left">Amount</th><th className="p-3 text-left">Rate</th><th className="p-3 text-left">Status</th><th className="p-3 text-left">Date</th><th className="p-3 text-left">Actions</th></tr>
                  </thead>
                  <tbody>
                    {commissions.map(c => (
                      <tr key={c.id} className="border-t">
                        <td className="p-3 text-xs font-mono">{c.auction_id.slice(0, 8)}...</td>
                        <td className="p-3">${c.amount.toFixed(2)}</td>
                        <td className="p-3">{(c.rate * 100).toFixed(0)}%</td>
                        <td className="p-3"><span className={`px-2 py-1 rounded text-xs ${statusColors[c.status] || 'bg-gray-100'}`}>{c.status}</span></td>
                        <td className="p-3">{new Date(c.created_at).toLocaleDateString()}</td>
                        <td className="p-3 space-x-2">
                          <button onClick={() => setConfirmDialog({ message: 'Complete this commission?', onConfirm: () => updateCommissionStatus(c.id, 'completed') })} className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700">Complete</button>
                          <button onClick={() => setConfirmDialog({ message: 'Fail this commission?', onConfirm: () => updateCommissionStatus(c.id, 'failed') })} className="text-xs bg-red-600 text-white px-2 py-1 rounded hover:bg-red-700">Fail</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==================== AUDIT LOGS ==================== */}
      {tab === 'audit' && (
        <div>
          <div className="flex gap-2 mb-4">
            <select className="border rounded px-4 py-2 text-sm" value={auditFilterAction} onChange={e => setAuditFilterAction(e.target.value)}>
              <option value="">All Actions</option>
              <option value="update_user_status">User Status</option>
              <option value="create_category">Create Category</option>
              <option value="update_category">Update Category</option>
              <option value="delete_category">Delete Category</option>
              <option value="update_ticket">Update Ticket</option>
              <option value="update_commission_status">Commission Status</option>
            </select>
          </div>
          {loadingAudit ? (
            <p className="text-gray-500">{t('loading')}</p>
          ) : auditLogs.length === 0 ? (
            <p className="text-gray-500 py-4">No audit logs.</p>
          ) : (
            <div className="bg-white rounded-lg shadow overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr><th className="p-3 text-left">Action</th><th className="p-3 text-left">Entity</th><th className="p-3 text-left">Details</th><th className="p-3 text-left">Admin</th><th className="p-3 text-left">Date</th></tr>
                </thead>
                <tbody>
                  {auditLogs.map(log => (
                    <tr key={log.id} className="border-t">
                      <td className="p-3"><span className="px-2 py-1 rounded text-xs bg-gray-100">{log.action}</span></td>
                      <td className="p-3 text-xs">{log.entity_type}/{log.entity_id?.slice(0, 8)}</td>
                      <td className="p-3 text-xs text-gray-600 max-w-xs truncate">{log.details || '—'}</td>
                      <td className="p-3 text-xs font-mono">{log.user_id ? log.user_id.slice(0, 8) + '...' : '—'}</td>
                      <td className="p-3 text-xs">{new Date(log.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}