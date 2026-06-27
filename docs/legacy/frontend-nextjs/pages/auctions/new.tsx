import { useState, useRef } from 'react';
import { useRouter } from 'next/router';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Layout from '@/components/Layout';
import { useTranslation } from 'react-i18next';

export default function CreateAuction() {
  const { t } = useTranslation();
  const router = useRouter();
  const { user } = useAuth();
  const [form, setForm] = useState({
    title: '', description: '', category_id: 1, start_price: 0, min_increment: 10,
    end_time: '', brand: '', model: '', year: '', mileage: '',
    fuel_type: '', transmission: '', damage_status: '',
    equipment_brand: '', serial_number: '', condition: '', location: ''
  });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!user || (user.role !== 'seller' && user.role !== 'corporate_seller')) {
    return <Layout><p className="text-red-500">Only sellers can create auctions.</p></Layout>;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = {
        ...form,
        year: form.year ? parseInt(form.year as string) : null,
        mileage: form.mileage ? parseInt(form.mileage as string) : null,
      };
      
      const auction: any = await api.post('/api/auctions', payload);
      
      const files = fileInputRef.current?.files;
      if (files && files.length > 0) {
        for (let i = 0; i < files.length; i++) {
          const fd = new FormData();
          fd.append('file', files[i]);
          fd.append('sort_order', i.toString());
          await api.upload(`/api/uploads?auction_id=${auction.id}`, fd);
        }
      }
      
      router.push('/');
    } catch (err: any) { 
      setError(err.message || t('error')); 
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">{t('nav_create')}</h1>
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input className="w-full border rounded px-4 py-2" placeholder={t('name')} value={form.title} onChange={e => setForm({...form, title: e.target.value})} required />
          <textarea className="w-full border rounded px-4 py-2" rows={4} placeholder="Description" value={form.description} onChange={e => setForm({...form, description: e.target.value})} required />
          
          <h2 className="font-semibold mt-4 text-gray-700">Pricing & Timing</h2>
          <div className="grid grid-cols-2 gap-4">
            <input className="border rounded px-4 py-2" type="number" step="0.01" placeholder="Start Price" value={form.start_price} onChange={e => setForm({...form, start_price: parseFloat(e.target.value)})} required />
            <input className="border rounded px-4 py-2" type="number" step="0.01" placeholder="Min Increment" value={form.min_increment} onChange={e => setForm({...form, min_increment: parseFloat(e.target.value)})} required />
            <input className="border rounded px-4 py-2 col-span-2" type="datetime-local" placeholder="End Time" value={form.end_time} onChange={e => setForm({...form, end_time: e.target.value})} required />
          </div>

          <h2 className="font-semibold mt-4 text-gray-700">Images</h2>
          <input type="file" multiple accept="image/*" ref={fileInputRef} className="w-full border rounded px-4 py-2" />

          <h2 className="font-semibold mt-4 text-gray-700">Vehicle Specs (Optional)</h2>
          <div className="grid grid-cols-2 gap-4">
            <input className="border rounded px-4 py-2" placeholder="Brand" value={form.brand} onChange={e => setForm({...form, brand: e.target.value})} />
            <input className="border rounded px-4 py-2" placeholder="Model" value={form.model} onChange={e => setForm({...form, model: e.target.value})} />
            <input className="border rounded px-4 py-2" type="number" placeholder="Year" value={form.year} onChange={e => setForm({...form, year: e.target.value})} />
            <input className="border rounded px-4 py-2" type="number" placeholder="Mileage (km)" value={form.mileage} onChange={e => setForm({...form, mileage: e.target.value})} />
            <input className="border rounded px-4 py-2" placeholder="Fuel Type" value={form.fuel_type} onChange={e => setForm({...form, fuel_type: e.target.value})} />
            <input className="border rounded px-4 py-2" placeholder="Transmission" value={form.transmission} onChange={e => setForm({...form, transmission: e.target.value})} />
            <input className="border rounded px-4 py-2 col-span-2" placeholder="Damage Status" value={form.damage_status} onChange={e => setForm({...form, damage_status: e.target.value})} />
          </div>

          <h2 className="font-semibold mt-4 text-gray-700">Equipment Specs (Optional)</h2>
          <div className="grid grid-cols-2 gap-4">
            <input className="border rounded px-4 py-2" placeholder="Equipment Brand" value={form.equipment_brand} onChange={e => setForm({...form, equipment_brand: e.target.value})} />
            <input className="border rounded px-4 py-2" placeholder="Serial Number" value={form.serial_number} onChange={e => setForm({...form, serial_number: e.target.value})} />
            <input className="border rounded px-4 py-2" placeholder="Condition" value={form.condition} onChange={e => setForm({...form, condition: e.target.value})} />
            <input className="border rounded px-4 py-2" placeholder="Location" value={form.location} onChange={e => setForm({...form, location: e.target.value})} />
          </div>

          <button disabled={isSubmitting} className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-blue-400 mt-6" type="submit">
            {isSubmitting ? t('loading') : t('submit')}
          </button>
        </form>
      </div>
    </Layout>
  );
}