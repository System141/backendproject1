import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  me: { translation: require('../public/locales/me/common.json') },
  en: { translation: require('../public/locales/en/common.json') },
};

if (!i18n.isInitialized) {
  i18n.use(initReactI18next).init({
    resources,
    lng: 'me',
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
  });
}

export default i18n;
