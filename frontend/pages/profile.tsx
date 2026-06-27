import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';
import { Notification } from '@/types';

export default function Profile() {
  const { t } = useTranslation();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [marketingConsent, setMarketingConsent] = useState(false);
  const [notifs, setNotifs] = useState<Notification[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
      return;
    }
    if (user) {
      setName(user.name || '');
      setPhone(user.phone || '');
      api.get<Notification[]>('/api/notifications')
        .then(setNotifs)
        .catch(() => {});
    }
  }, [user, loading, router]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setMessage('');
    setError('');
    try {
      const res = await api.put<any>('/api/users/me', {
        name: name || undefined,
        phone: phone || undefined,
        marketing_consent: marketingConsent,
      });
      setName(res.name || '');
      setPhone(res.phone || '');
      setMessage(t('profile_save_success') || 'Profile updated');
    } catch (err: any) {
      setError(err?.message || t('error'));
    } finally {
      setIsSaving(false);
    }
  };

  const markRead = async (id: string) => {
    await api.put(`/api/notifications/${id}/read`, {});
    setNotifs(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
  };

  if (loading || !user) return <Layout><p className="p-6">{t('loading')}</p></Layout>;

  return (
    <Layout>
      <div className="max-w-2xl mx-auto space-y-8">
        {/* Profile Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold mb-2">{t('profile_title')}</h1>
          <p className="text-gray-500">{t('profile_desc')}</p>
        </div>

        {/* User Info */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">{t('account_info') || 'Account Information'}</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">{t('name')}</span>
              <p className="font-medium">{user.name}</p>
            </div>
            <div>
              <span className="text-gray-500">{t('email')}</span>
              <p className="font-medium">{user.email}</p>
            </div>
            <div>
              <span className="text-gray-500">{t('phone')}</span>
              <p className="font-medium">{user.phone || '-'}</p>
            </div>
            <div>
              <span className="text-gray-500">{t('role')}</span>
              <p className="font-medium capitalize">{user.role}</p>
            </div>
            <div>
              <span className="text-gray-500">{t('status')}</span>
              <p className="font-medium capitalize">{user.status}</p>
            </div>
          </div>
        </div>

        {/* Edit Profile Form */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">{t('profile_edit') || 'Edit Profile'}</h2>
          {message && (
            <div className="mb-4 p-3 bg-green-50 text-green-700 rounded border border-green-200 text-sm">{message}</div>
          )}
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded border border-red-200 text-sm">{error}</div>
          )}
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('name')}</label>
              <input
                type="text"
                className="w-full border rounded px-4 py-2"
                value={name}
                onChange={e => setName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('phone')}</label>
              <input
                type="tel"
                className="w-full border rounded px-4 py-2"
                value={phone}
                onChange={e => setPhone(e.target.value)}
              />
            </div>
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={marketingConsent}
                onChange={e => setMarketingConsent(e.target.checked)}
                className="mt-1"
              />
              <span className="text-sm text-gray-600">{t('register_marketing')}</span>
            </label>
            <button
              type="submit"
              disabled={isSaving}
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:bg-blue-400"
            >
              {isSaving ? t('loading') : t('profile_save')}
            </button>
          </form>
        </div>

        {/* Notifications */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">{t('notifications')}</h2>
          {notifs.length === 0 ? (
            <p className="text-gray-500">{t('no_notifications')}</p>
          ) : (
            <div className="space-y-3">
              {notifs.map(n => (
                <div key={n.id} className={`p-4 rounded-lg border ${n.is_read ? 'opacity-60 bg-gray-50' : 'bg-white'}`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{n.title}</p>
                      <p className="text-sm text-gray-600">{n.message}</p>
                      <p className="text-xs text-gray-400 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                    </div>
                    {!n.is_read && (
                      <button onClick={() => markRead(n.id)} className="text-xs text-blue-600 hover:underline whitespace-nowrap ml-4">
                        {t('mark_read')}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}