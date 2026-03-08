import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { searchProducts, createProduct, updateProduct, adjustStock, getCategories } from '../api/catalog'
import styles from './Pages.module.css'
import tableStyles from './Table.module.css'

// Spanish VAT rates (Ley 37/1992 del IVA)
// 0% exempt, 4% superreducido, 5% reduced special, 10% reducido, 21% general
const VAT_RATES = [
  { value: '0.00',  labelKey: 'vatRates.exempt' },
  { value: '0.04',  labelKey: 'vatRates.superReduced' },
  { value: '0.05',  labelKey: 'vatRates.reduced5' },
  { value: '0.10',  labelKey: 'vatRates.reduced10' },
  { value: '0.21',  labelKey: 'vatRates.standard' },
]

const EMPTY = { name: '', sku: '', barcode: '', price: '', cost: '', tax_rate: '0.21', stock: '0', category: '', description: '' }

export default function CatalogPage() {
  const { t } = useTranslation()
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const load = async (q = search) => {
    setLoading(true)
    try {
      const data = await searchProducts({ search: q, page_size: 100 })
      setProducts(Array.isArray(data) ? data : data.results ?? data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load('')
    getCategories().then(setCategories).catch(() => {})
  }, [])

  const handleSearch = (e) => {
    setSearch(e.target.value)
    clearTimeout(window._catalogDebounce)
    window._catalogDebounce = setTimeout(() => load(e.target.value), 300)
  }

  const openNew = () => { setEditing('new'); setForm(EMPTY); setError(null) }
  const openEdit = (p) => { setEditing(p); setForm({ ...p, price: String(p.price), cost: String(p.cost), tax_rate: String(p.tax_rate), stock: String(p.stock) }); setError(null) }

  const handleSave = async () => {
    setSaving(true); setError(null)
    try {
      const payload = { ...form, price: parseFloat(form.price), cost: parseFloat(form.cost || 0), tax_rate: parseFloat(form.tax_rate), stock: parseInt(form.stock) }
      if (editing === 'new') await createProduct(payload)
      else await updateProduct(editing.id, payload)
      setEditing(null)
      load()
    } catch (e) { setError(e.message) }
    finally { setSaving(false) }
  }

  const handleStockAdjust = async (product, delta) => {
    try {
      const updated = await adjustStock(product.id, delta)
      setProducts((prev) => prev.map((p) => p.id === updated.id ? updated : p))
    } catch (e) { alert(e.message) }
  }

  const textFields = [
    [t('catalog.fieldName'), 'name'],
    [t('catalog.fieldSku'), 'sku'],
    [t('catalog.fieldBarcode'), 'barcode'],
    [t('catalog.fieldCategory'), 'category'],
    [t('catalog.fieldDescription'), 'description'],
  ]
  const numFields = [
    [t('catalog.fieldPrice'), 'price'],
    [t('catalog.fieldCost'), 'cost'],
    [t('catalog.fieldStock'), 'stock'],
  ]

  return (
    <div className={styles.pageWrapper}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>{t('catalog.title')}</h1>
        <input className={tableStyles.searchInput} placeholder={t('catalog.searchPlaceholder')} value={search} onChange={handleSearch} />
        <button className={tableStyles.primaryBtn} onClick={openNew}>{t('catalog.newProduct')}</button>
      </div>

      <div className={tableStyles.tableWrapper}>
        <table className={tableStyles.table}>
          <thead>
            <tr>
              <th>{t('catalog.colName')}</th>
              <th>{t('catalog.colSku')}</th>
              <th>{t('catalog.colPrice')}</th>
              <th>{t('catalog.colVat')}</th>
              <th>{t('catalog.colStock')}</th>
              <th>{t('catalog.colCategory')}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className={tableStyles.empty}>{t('catalog.loading')}</td></tr>
            ) : products.length === 0 ? (
              <tr><td colSpan={7} className={tableStyles.empty}>{t('catalog.noProducts')}</td></tr>
            ) : products.map((p) => (
              <tr key={p.id} style={{ opacity: p.active === false ? 0.5 : 1 }}>
                <td>{p.name}</td>
                <td className={tableStyles.mono}>{p.sku}</td>
                <td>{p.price.toFixed(2)}</td>
                <td>{Math.round(parseFloat(p.tax_rate ?? 0.21) * 100)}%</td>
                <td>
                  <div className={tableStyles.stockRow}>
                    <button onClick={() => handleStockAdjust(p, -1)} disabled={p.stock < 1}>−</button>
                    <span>{p.stock}</span>
                    <button onClick={() => handleStockAdjust(p, 1)}>+</button>
                  </div>
                </td>
                <td>{p.category}</td>
                <td><button className={tableStyles.editBtn} onClick={() => openEdit(p)}>{t('catalog.edit')}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing !== null && (
        <div className={tableStyles.modalOverlay} onClick={(e) => e.target === e.currentTarget && setEditing(null)}>
          <div className={tableStyles.modal}>
            <div className={tableStyles.modalHeader}>
              <h3>{editing === 'new' ? t('catalog.newProductTitle') : t('catalog.editProductTitle')}</h3>
              <button onClick={() => setEditing(null)}>✕</button>
            </div>
            <div className={tableStyles.modalBody}>
              {textFields.map(([label, key]) => (
                <label key={key} className={tableStyles.field}>
                  <span>{label}</span>
                  <input className={tableStyles.input} value={form[key]} onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))} />
                </label>
              ))}
              {numFields.map(([label, key]) => (
                <label key={key} className={tableStyles.field}>
                  <span>{label}</span>
                  <input className={tableStyles.input} type="number" step="0.01" min="0" value={form[key]} onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))} />
                </label>
              ))}
              <label className={tableStyles.field}>
                <span>{t('vatRates.selectorLabel')}</span>
                <select
                  className={tableStyles.input}
                  value={form.tax_rate}
                  onChange={(e) => setForm((f) => ({ ...f, tax_rate: e.target.value }))}
                >
                  {VAT_RATES.map(({ value, labelKey }) => (
                    <option key={value} value={value}>{t(labelKey)}</option>
                  ))}
                </select>
              </label>
              {error && <p className={tableStyles.error}>{error}</p>}
            </div>
            <div className={tableStyles.modalFooter}>
              <button className={tableStyles.cancelBtn} onClick={() => setEditing(null)}>{t('catalog.cancel')}</button>
              <button className={tableStyles.primaryBtn} onClick={handleSave} disabled={saving}>
                {saving ? t('catalog.saving') : t('catalog.save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
