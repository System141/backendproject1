import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';

export default function ContactPage() {
  const { t } = useTranslation();
  const [sent, setSent] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSent(true);
    setTimeout(() => setSent(false), 3000);
  };

  return (
    <Layout>
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white rounded-2xl p-8 sm:p-12 mb-8">
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight mb-3">{t('contact_title')}</h1>
        <p className="text-gray-300 text-lg max-w-2xl">{t('contact_desc')}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">{t('contact_form_name')}</label>
              <input
                required
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none"
                placeholder={t('contact_form_name')}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">{t('contact_form_email')}</label>
              <input
                required
                type="email"
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none"
                placeholder="email@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">{t('contact_form_msg')}</label>
              <textarea
                required
                rows={5}
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none resize-y"
                placeholder={t('contact_form_msg')}
              />
            </div>
            <button
              type="submit"
              className="bg-red-600 hover:bg-red-500 text-white font-bold px-6 py-3 rounded-lg transition"
            >
              {t('contact_btn_send')}
            </button>
            {sent && (
              <p className="text-green-600 text-sm font-semibold mt-2">
                ✓ {t('contact_desc')}
              </p>
            )}
          </div>
        </form>

        <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
          <h3 className="text-xl font-bold text-gray-900 mb-6">{t('contact_info')}</h3>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <span className="text-gray-400 text-lg">📧</span>
              <div>
                <p className="text-sm text-gray-500">{t('contact_form_email')}</p>
                <p className="font-semibold text-gray-900">{t('contact_email')}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-gray-400 text-lg">📞</span>
              <div>
                <p className="text-sm text-gray-500">{t('contact_info')}</p>
                <p className="font-semibold text-gray-900">{t('contact_phone')}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-gray-400 text-lg">📍</span>
              <div>
                <p className="text-sm text-gray-500">{t('detail_loc')}</p>
                <p className="font-semibold text-gray-900">{t('contact_address')}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}