import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import { useTranslation } from 'react-i18next';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (user) {
      api.get<{count: number}>('/api/notifications/unread-count')
        .then(r => setUnreadCount(r.count))
        .catch(() => {});
    }
  }, [user]);

  const toggleLang = () => {
    const next = i18n.language === 'me' ? 'en' : 'me';
    i18n.changeLanguage(next);
    router.push(router.pathname, router.asPath, { locale: next });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-xl font-bold text-blue-600">BidMont</Link>
              {user && (
                <>
                  <Link href="/auctions/new" className="text-gray-700 hover:text-blue-600">{t('nav_create')}</Link>
                  {(user.role === 'seller' || user.role === 'corporate_seller') && (
                    <Link href="/my-auctions" className="text-gray-700 hover:text-blue-600">{t('nav_my_auctions')}</Link>
                  )}
                  {user.role === 'admin' && (
                    <Link href="/admin" className="text-gray-700 hover:text-blue-600">{t('nav_admin')}</Link>
                  )}
                </>
              )}
            </div>
            <div className="flex items-center space-x-4">
              <button onClick={toggleLang} className="text-sm text-gray-500 hover:text-gray-700">
                {i18n.language === 'me' ? 'EN' : 'ME'}
              </button>
              {user ? (
                <>
                  <Link href="/profile" className="relative text-gray-700 hover:text-blue-600">
                    🔔
                    {unreadCount > 0 && (
                      <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </span>
                    )}
                  </Link>
                  <Link href="/profile" className="text-gray-700 hover:text-blue-600">{t('nav_profile')}</Link>
                  <button onClick={() => { logout(); router.push('/login'); }} className="text-gray-700 hover:text-red-600">{t('nav_logout')}</button>
                </>
              ) : (
                <>
                  <Link href="/login" className="text-gray-700 hover:text-blue-600">{t('nav_login')}</Link>
                  <Link href="/register" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">{t('nav_register')}</Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}