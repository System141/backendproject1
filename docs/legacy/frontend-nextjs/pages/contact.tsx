import { useState } from 'react';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';
import { api } from '@/lib/api';

export default function ContactPage() {
  const { t } = useTranslation();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [msg, setMsg] = useState('');
  const [sent, setSent] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    setError('');
    try {
      await api.post('/api/support/contact', {
        subject: `Contact form from ${name} (${email})`,
        message: msg,
      });
      setSent(true);
      setTimeout(() => setSent(false), 5000);
      setName('');
      setEmail('');
      setMsg('');
    } catch {
      setError(t('error'));
    } finally {
      setSending(false);
    }
  };

  return (
    <Layout>
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white rounded-2xl p-8 sm:p-12 mb-8">
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight mb-3">{t('contact_title')}</h1>
        <p className="text-gray-300 text-lg max-w-2xl">{t('contact_desc')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
            {sent && (
              <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
                {t('submit')} ✓
              </div>
            )}
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('contact_form_name')}</label>
              <input
                className="w-full border rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none"
                value={name}
                onChange={e => setName(e.target.value)}
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('contact_form_email')}</label>
              <input
                type="email"
                className="w-full border rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('contact_form_msg')}</label>
              <textarea
                className="w-full border rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none min-h-[120px]"
                value={msg}
                onChange={e => setMsg(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              disabled={sending}
              className="bg-red-600 hover:bg-red-500 disabled:bg-gray-400 text-white font-bold px-6 py-3 rounded-lg transition text-sm"
            >
              {sending ? t('loading') : t('contact_btn_send')}
            </button>
          </form>
        </div>

        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <h3 className="font-bold text-gray-900 mb-3">{t('contact_info')}</h3>
            <div className="space-y-3 text-sm text-gray-600">
              <p>📧 {t('contact_email')}</p>
              <p>📞 {t('contact_phone')}</p>
              <p>📍 {t('contact_address')}</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}