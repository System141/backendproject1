import Layout from '@/components/Layout';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';

export default function HowItWorksPage() {
  const { t } = useTranslation();

  const steps = [
    { num: '01', title: t('how_step1_title'), desc: t('how_step1_desc') },
    { num: '02', title: t('how_step2_title'), desc: t('how_step2_desc') },
    { num: '03', title: t('how_step3_title'), desc: t('how_step3_desc') },
    { num: '04', title: t('how_step4_title'), desc: t('how_step4_desc') },
  ];

  return (
    <Layout>
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white rounded-2xl p-8 sm:p-12 mb-8">
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight mb-3">{t('how_page_title')}</h1>
        <p className="text-gray-300 text-lg max-w-2xl">{t('how_page_desc')}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {steps.map(step => (
          <div key={step.num} className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
            <div className="text-5xl font-black text-gray-200 mb-4">{step.num}</div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">{step.title}</h3>
            <p className="text-gray-600 leading-relaxed">{step.desc}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-2xl p-8 text-center">
        <h3 className="text-xl font-bold text-gray-900 mb-3">{t('how_title')}</h3>
        <p className="text-gray-600 mb-6">{t('how_desc')}</p>
        <Link href="/auctions" className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white font-bold px-6 py-3 rounded-lg transition">
          {t('hero_btn1')}
        </Link>
      </div>
    </Layout>
  );
}