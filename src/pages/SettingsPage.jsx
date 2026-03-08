import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { getConfig, updateConfig } from '../api/config'
import { listProviders } from '../api/payments'
import useConfigStore from '../store/configStore'
import { LANGUAGES } from '../i18n'
import styles from './Pages.module.css'
import tableStyles from './Table.module.css'

export default function SettingsPage() {
  const { setConfig } = useConfigStore()
  const { t, i18n } = useTranslation()
  const [config, setLocal] = useState(null)
  const [providers, setProviders] = useState([])
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [providerConfigs, setProviderConfigs] = useState({})

  useEffect(() => {
    getConfig().then((c) => { setLocal(c); setProviderConfigs(c.payment_configs ?? {}) })
    listProviders().then(setProviders).catch(() => {})
  }, [])

  if (!config) return <div style={{ padding: '2rem', color: 'var(--text-muted)' }}>{t('settings.loading')}</div>

  const setShop = (k, v) => setLocal((c) => ({ ...c, shop: { ...c.shop, [k]: v } }))
  const setReceipt = (k, v) => setLocal((c) => ({ ...c, receipt: { ...c.receipt, [k]: v } }))
  const toggleProvider = (id) => {
    const active = config.active_payment_methods ?? []
    setLocal((c) => ({
      ...c,
      active_payment_methods: active.includes(id) ? active.filter((x) => x !== id) : [...active, id],
    }))
  }
  const setProviderConfig = (id, key, value) => {
    setProviderConfigs((prev) => ({ ...prev, [id]: { ...(prev[id] ?? {}), [key]: value } }))
  }

  const handleSave = async () => {
    setSaving(true); setSaved(false)
    try {
      const updated = await updateConfig({ ...config, payment_configs: providerConfigs })
      setLocal(updated); setConfig(updated); setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } finally { setSaving(false) }
  }

  const shopFields = [
    [t('settings.fieldShopName'), 'name'],
    [t('settings.fieldAddress'), 'address'],
    [t('settings.fieldPhone'), 'phone'],
    [t('settings.fieldTaxId'), 'tax_id'],
    [t('settings.fieldWebsite'), 'website'],
    [t('settings.fieldReceiptFooter'), 'receipt_footer'],
  ]

  return (
    <div className={styles.pageWrapper}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>{t('settings.title')}</h1>
        <button className={tableStyles.primaryBtn} onClick={handleSave} disabled={saving}>
          {saving ? t('settings.saving') : saved ? t('settings.saved') : t('settings.saveChanges')}
        </button>
      </div>

      <div style={{ padding: '1.25rem', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '640px' }}>

        {/* Shop */}
        <section>
          <h2 className={tableStyles.sectionTitle}>{t('settings.shopInfo')}</h2>
          {shopFields.map(([label, key]) => (
            <label key={key} className={tableStyles.field}>
              <span>{label}</span>
              <input className={tableStyles.input} value={config.shop[key] ?? ''} onChange={(e) => setShop(key, e.target.value)} />
            </label>
          ))}
        </section>

        {/* Regional */}
        <section>
          <h2 className={tableStyles.sectionTitle}>{t('settings.regional')}</h2>
          <label className={tableStyles.field}>
            <span>{t('settings.fieldCurrency')}</span>
            <input className={tableStyles.input} value={config.currency} onChange={(e) => setLocal((c) => ({ ...c, currency: e.target.value }))} />
          </label>
          <label className={tableStyles.field}>
            <span>{t('settings.fieldLocale')}</span>
            <input className={tableStyles.input} value={config.locale} onChange={(e) => setLocal((c) => ({ ...c, locale: e.target.value }))} />
          </label>
        </section>

        {/* Receipt */}
        <section>
          <h2 className={tableStyles.sectionTitle}>{t('settings.receipt')}</h2>
          <label className={tableStyles.field}>
            <span>{t('settings.fieldPaperWidth')}</span>
            <input className={tableStyles.input} type="number" min="58" max="112" value={config.receipt?.paper_width_mm ?? 80} onChange={(e) => setReceipt('paper_width_mm', parseInt(e.target.value))} />
          </label>
          <label className={tableStyles.field} style={{ flexDirection: 'row', alignItems: 'center' }}>
            <input type="checkbox" checked={config.receipt?.show_vat_breakdown ?? true} onChange={(e) => setReceipt('show_vat_breakdown', e.target.checked)} />
            <span style={{ marginLeft: '0.5rem' }}>{t('settings.fieldShowVat')}</span>
          </label>
        </section>

        {/* Payment providers */}
        <section>
          <h2 className={tableStyles.sectionTitle}>{t('settings.paymentMethods')}</h2>
          {providers.map((provider) => {
            const isActive = (config.active_payment_methods ?? []).includes(provider.id)
            const cfg = providerConfigs[provider.id] ?? {}
            return (
              <div key={provider.id} className={tableStyles.providerCard}>
                <div className={tableStyles.providerHeader}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input type="checkbox" checked={isActive} onChange={() => toggleProvider(provider.id)} />
                    <span style={{ fontWeight: 600 }}>{provider.name}</span>
                  </label>
                  {provider.requires_network && (
                    <span className={tableStyles.badge} style={{ background: 'rgba(99,102,241,0.15)', color: 'var(--accent)' }}>
                      {t('settings.online')}
                    </span>
                  )}
                </div>
                {isActive && provider.config_schema.length > 0 && (
                  <div className={tableStyles.providerFields}>
                    {provider.config_schema.map((field) => (
                      <label key={field.key} className={tableStyles.field}>
                        <span>{field.label}{field.required && <span style={{ color: 'var(--danger)' }}> *</span>}</span>
                        <input
                          className={tableStyles.input}
                          type={field.type === 'password' ? 'password' : 'text'}
                          placeholder={field.help_text}
                          value={cfg[field.key] ?? ''}
                          onChange={(e) => setProviderConfig(provider.id, field.key, e.target.value)}
                        />
                      </label>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </section>

        {/* Language */}
        <section>
          <h2 className={tableStyles.sectionTitle}>{t('settings.language')}</h2>
          <label className={tableStyles.field}>
            <span>{t('settings.fieldLanguage')}</span>
            <select
              className={tableStyles.input}
              value={i18n.resolvedLanguage}
              onChange={(e) => i18n.changeLanguage(e.target.value)}
            >
              {LANGUAGES.map(({ code, label }) => (
                <option key={code} value={code}>{label}</option>
              ))}
            </select>
          </label>
        </section>

      </div>
    </div>
  )
}
