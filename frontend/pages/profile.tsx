import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface Notification { id: string; type: string; title: string; message: string; is_read: boolean; created_at: string; }

export default function Profile() {
  const { t } = useTranslation();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [notifs, setNotifs] = useState<Notification[]>([]);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
    if (user) api.get<Notification[]>('/api/notifications').then(setNotifs).catch(console.error);
  }, [user, loading, router]);

  const markRead = async (id: string) => {
    await api.put(`/api/notifications/${id}/read`, {});
    setNotifs(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
  };

  if (loading || !user) return <Layout><p>{t('loading')}</p></Layout>;

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">{t('nav_profile')}</h1>
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <p><strong>Name:</strong> {user.name}</p>
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>Phone:</strong> {user.phone || '-'}</p>
          <p><strong>Role:</strong> {user.role}</p>
        </div>
        <h2 className="text-xl font-bold mb-4">{t('notifications')}</h2>
        {notifs.length === 0 ? <p className="text-gray-500">{t('no_notifications')}</p> : (
          <div className="space-y-3">
            {notifs.map(n => (
              <div key={n.id} className={`bg-white rounded-lg shadow p-4 ${n.is_read ? 'opacity-60' : ''}`}>
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium">{n.title}</p>
                    <p className="text-sm text-gray-600">{n.message}</p>
                    <p className="text-xs text-gray-400 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                  </div>
                  {!n.is_read && (
                    <button onClick={() => markRead(n.id)} className="text-xs text-blue-600 hover:underline">{t('mark_read')}</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
