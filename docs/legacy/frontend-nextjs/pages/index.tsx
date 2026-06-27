import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import Layout from '@/components/Layout';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import { Auction } from '@/types';

export default function Home() {
  const { t } = useTranslation();
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (category) params.set('category_id', category);
    api.get<Auction[]>(`/api/auctions?${params}`)
      .then(data => setAuctions(data))
      .catch(() => setError(t('error')))
      .finally(() => setLoading(false));
  }, [search, category, t]);

  const categories = [
    { href: '/vehicles', title: t('cat_vehicles_title'), desc: t('cat_vehicles_desc'), color: 'from-blue-900 to-blue-700' },
    { href: '/equipment', title: t('cat_equipment_title'), desc: t('cat_equipment_desc'), color: 'from-red-600 to-red-500' },
    { href: '/general', title: t('cat_general_title'), desc: t('cat_general_desc'), color: 'from-blue-900 to-blue-700' },
  ];

  return (
    <Layout>
      {/* Hero Section */}
      <section className="relative min-h-[70vh] flex items-center bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 text-white overflow-hidden">
        <div className="absolute inset-0 opacity-20" style={{
          backgroundImage: "url('https://images.unsplash.com/photo-1568745495188-2d6c99d14533?auto=format&fit=crop&w=1900&q=80')",
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }} />
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-white/80 text-xs font-semibold uppercase tracking-widest mb-6">
              <span className="w-2 h-2 bg-white rounded-full" />
              {t('hero_badge')}
            </span>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-none mb-6">
              {t('hero_title1')}{' '}
              <span className="text-red-500 block">{t('hero_title2')}</span>
              <span>{t('hero_title3')}</span>
            </h1>
            <p className="text-lg text-gray-300 max-w-xl mb-8 leading-relaxed">
              {t('hero_sub')}
            </p>
            <div className="flex flex-wrap gap-3">
              <Link href="/auctions" className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white font-bold px-6 py-3 rounded-lg transition shadow-lg shadow-red-600/30">
                {t('hero_btn1')}
              </Link>
              <Link href="/auctions/new" className="inline-flex items-center gap-2 border border-white/30 hover:bg-white/10 text-white font-bold px-6 py-3 rounded-lg transition">
                {t('hero_btn2')}
              </Link>
            </div>
            <div className="flex gap-10 mt-12 flex-wrap">
              <div>
                <div className="text-3xl font-black">{auctions.length || '1.2k'}+</div>
                <div className="text-xs text-gray-400 uppercase tracking-widest font-semibold mt-1">{t('hero_stat1')}</div>
              </div>
              <div>
                <div className="text-3xl font-black">€8M+</div>
                <div className="text-xs text-gray-400 uppercase tracking-widest font-semibold mt-1">{t('hero_stat2')}</div>
              </div>
              <div>
                <div className="text-3xl font-black">340+</div>
                <div className="text-xs text-gray-400 uppercase tracking-widest font-semibold mt-1">{t('hero_stat3')}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-end justify-between mb-10">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">{t('how_title')}</h2>
              <p className="text-gray-500 mt-2">{t('how_desc')}</p>
            </div>
            <Link href="/how-it-works" className="hidden sm:inline-flex items-center gap-2 bg-gray-900 hover:bg-gray-800 text-white font-bold px-5 py-2.5 rounded-lg transition text-sm">
              {t('how_btn')}
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="bg-gray-50 border border-gray-100 rounded-2xl p-6">
                <div className="text-3xl font-black text-gray-900 mb-3">0{i}</div>
                <p className="text-gray-600 leading-relaxed text-sm">{t(`how_b${i}`)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Category Strip */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {categories.map(cat => (
              <Link key={cat.href} href={cat.href} className={`bg-gradient-to-br ${cat.color} rounded-2xl p-8 text-white min-h-[180px] flex flex-col justify-between transition hover:scale-[1.02]`}>
                <div>
                  <h3 className="text-2xl font-bold">{cat.title}</h3>
                  <p className="text-white/70 mt-2 leading-relaxed text-sm">{cat.desc}</p>
                </div>
                <span className="font-bold text-sm mt-4">{t('cat_view')}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Active Auctions */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-4 mb-6">
            <input
              className="flex-1 border rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none"
              placeholder={t('search')}
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            <input
              className="w-40 border rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none"
              placeholder={t('categories')}
              value={category}
              onChange={e => setCategory(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {loading && (
              <div className="col-span-full text-center py-16">
                <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
                <p className="mt-4 text-gray-500">{t('loading')}</p>
              </div>
            )}
            {error && (
              <div className="col-span-full text-center py-16 text-red-500">
                <p className="text-lg">{error}</p>
              </div>
            )}
            {!loading && !error && auctions.length === 0 && (
              <div className="col-span-full text-center py-16 text-gray-500">
                <p className="text-lg">{t('no_results')}</p>
              </div>
            )}
            {!loading && !error && auctions.map(a => (
              <Link key={a.id} href={`/auctions/${a.id}`} className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition p-6 flex flex-col">
                {a.images && a.images.length > 0 && (
                  <img src={a.images[0].image_url} alt={a.title} className="w-full h-40 object-cover rounded-lg mb-4" />
                )}
                <h2 className="text-lg font-semibold mb-2 text-gray-900">{a.title}</h2>
                <p className="text-2xl font-bold text-blue-600">${a.current_price.toFixed(2)}</p>
                <p className="text-sm text-gray-500 mt-2">{t('end_time')}: {new Date(a.end_time).toLocaleString()}</p>
                {a.brand && <p className="text-sm text-gray-500">{a.brand} {a.model} ({a.year})</p>}
                {a.equipment_brand && <p className="text-sm text-gray-500">{a.equipment_brand} — {a.condition}</p>}
                <span className={`inline-block mt-auto pt-2 px-2.5 py-1 text-xs font-semibold rounded-full self-start ${
                  a.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                }`}>{a.status}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </Layout>
  );
}