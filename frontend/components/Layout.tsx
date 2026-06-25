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
  const [mobileOpen, setMobileOpen] = useState(false);

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

  const navLinks = [
    { href: '/', label: 'nav_home' },
    { href: '/auctions', label: 'nav_auctions' },
    { href: '/vehicles', label: 'nav_vehicles' },
    { href: '/equipment', label: 'nav_equipment' },
    { href: '/general', label: 'nav_general' },
    { href: '/how-it-works', label: 'nav_how' },
    { href: '/about', label: 'nav_about' },
    { href: '/contact', label: 'nav_contact' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-xl font-bold text-blue-600">BidMont</Link>
              {/* Desktop nav links */}
              <div className="hidden md:flex items-center space-x-4">
                {navLinks.map(link => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`text-sm font-medium transition ${
                      router.pathname === link.href
                        ? 'text-red-600'
                        : 'text-gray-700 hover:text-blue-600'
                    }`}
                  >
                    {t(link.label)}
                  </Link>
                ))}
                {user && (
                  <>
                    <Link href="/auctions/new" className="text-sm font-medium text-gray-700 hover:text-blue-600 transition">{t('nav_create')}</Link>
                    {(user.role === 'seller' || user.role === 'corporate_seller') && (
                      <Link href="/my-auctions" className="text-sm font-medium text-gray-700 hover:text-blue-600 transition">{t('nav_my_auctions')}</Link>
                    )}
                    {user.role === 'admin' && (
                      <Link href="/admin" className="text-sm font-medium text-gray-700 hover:text-blue-600 transition">{t('nav_admin')}</Link>
                    )}
                  </>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button onClick={toggleLang} className="text-sm text-gray-500 hover:text-gray-700 font-medium">
                {i18n.language === 'me' ? 'EN' : 'ME'}
              </button>
              {user ? (
                <div className="hidden md:flex items-center space-x-4">
                  <Link href="/profile" className="relative text-gray-700 hover:text-blue-600 transition">
                    🔔
                    {unreadCount > 0 && (
                      <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </span>
                    )}
                  </Link>
                  <Link href="/profile" className="text-sm font-medium text-gray-700 hover:text-blue-600 transition">{t('nav_profile')}</Link>
                  <button onClick={() => { logout(); router.push('/login'); }} className="text-sm font-medium text-gray-700 hover:text-red-600 transition">{t('nav_logout')}</button>
                </div>
              ) : (
                <div className="hidden md:flex items-center space-x-4">
                  <Link href="/login" className="text-sm font-medium text-gray-700 hover:text-blue-600 transition">{t('nav_login')}</Link>
                  <Link href="/register" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm font-medium transition">{t('nav_register')}</Link>
                </div>
              )}
              {/* Mobile menu button */}
              <button
                onClick={() => setMobileOpen(!mobileOpen)}
                className="md:hidden text-gray-700 hover:text-blue-600 focus:outline-none"
                aria-label="Toggle menu"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {mobileOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>
          </div>
          {/* Mobile menu */}
          {mobileOpen && (
            <div className="md:hidden pb-4 border-t border-gray-100 pt-2">
              {navLinks.map(link => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={`block py-2 text-sm font-medium transition ${
                    router.pathname === link.href
                      ? 'text-red-600'
                      : 'text-gray-700 hover:text-blue-600'
                  }`}
                >
                  {t(link.label)}
                </Link>
              ))}
              {user ? (
                <>
                  <Link href="/auctions/new" onClick={() => setMobileOpen(false)} className="block py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition">{t('nav_create')}</Link>
                  <Link href="/profile" onClick={() => setMobileOpen(false)} className="block py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition">{t('nav_profile')}</Link>
                  <button onClick={() => { logout(); router.push('/login'); setMobileOpen(false); }} className="block py-2 text-sm font-medium text-gray-700 hover:text-red-600 transition">{t('nav_logout')}</button>
                </>
              ) : (
                <>
                  <Link href="/login" onClick={() => setMobileOpen(false)} className="block py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition">{t('nav_login')}</Link>
                  <Link href="/register" onClick={() => setMobileOpen(false)} className="block py-2 text-sm font-medium text-blue-600 hover:text-blue-700 transition">{t('nav_register')}</Link>
                </>
              )}
            </div>
          )}
        </div>
      </nav>
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {children}
      </main>
      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-white font-bold text-lg mb-3">BidMont</h3>
              <p className="text-sm">{t('footer_text')}</p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-3 text-sm uppercase tracking-wider">{t('nav_auctions')}</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/vehicles" className="hover:text-white transition">{t('nav_vehicles')}</Link></li>
                <li><Link href="/equipment" className="hover:text-white transition">{t('nav_equipment')}</Link></li>
                <li><Link href="/general" className="hover:text-white transition">{t('nav_general')}</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-3 text-sm uppercase tracking-wider">{t('nav_about')}</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/how-it-works" className="hover:text-white transition">{t('nav_how')}</Link></li>
                <li><Link href="/about" className="hover:text-white transition">{t('nav_about')}</Link></li>
                <li><Link href="/contact" className="hover:text-white transition">{t('nav_contact')}</Link></li>
                <li><Link href="/admin" className="hover:text-white transition">{t('footer_admin')}</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm">
            <p>&copy; {new Date().getFullYear()} BidMont. {t('footer_text')}.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}