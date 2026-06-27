import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';

export default function AboutPage() {
  const { t } = useTranslation();

  return (
    <Layout>
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white rounded-2xl p-8 sm:p-12 mb-8">
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight mb-3">{t('about_title')}</h1>
        <p className="text-gray-300 text-lg max-w-2xl">{t('about_desc')}</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl p-8 sm:p-12 shadow-sm">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">{t('about_mission_title')}</h2>
        <p className="text-gray-600 leading-relaxed text-lg">
          {t('about_mission_desc')}
        </p>
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="bg-gray-50 rounded-xl p-6 border border-gray-100">
            <div className="text-3xl mb-3">🎯</div>
            <h3 className="font-bold text-gray-900 mb-2">{t('about_mission_title')}</h3>
            <p className="text-sm text-gray-600">{t('about_mission_desc')}</p>
          </div>
          <div className="bg-gray-50 rounded-xl p-6 border border-gray-100">
            <div className="text-3xl mb-3">🤝</div>
            <h3 className="font-bold text-gray-900 mb-2">{t('hero_stat3')}</h3>
            <p className="text-sm text-gray-600">{t('hero_sub')}</p>
          </div>
          <div className="bg-gray-50 rounded-xl p-6 border border-gray-100">
            <div className="text-3xl mb-3">🌍</div>
            <h3 className="font-bold text-gray-900 mb-2">{t('hero_stat2')}</h3>
            <p className="text-sm text-gray-600">{t('cat_general_desc')}</p>
          </div>
        </div>
      </div>
    </Layout>
  );
}