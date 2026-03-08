import { useState, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { searchProducts } from '../../api/catalog'
import styles from './POS.module.css'

export default function SearchPanel({ onAddItem }) {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef(null)

  const search = useCallback(async (q) => {
    if (!q.trim()) { setResults([]); return }
    setLoading(true)
    try {
      const data = await searchProducts({ search: q, in_stock: true, page_size: 20 })
      const items = Array.isArray(data) ? data : data.results ?? data
      setResults(items)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  const handleChange = (e) => {
    const q = e.target.value
    setQuery(q)
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => search(q), 300)
  }

  const clear = () => { setQuery(''); setResults([]) }

  return (
    <div className={styles.panel}>
      <h2 className={styles.panelTitle}>{t('search.title')}</h2>

      <div className={styles.searchRow}>
        <input
          className={styles.searchInput}
          placeholder={t('search.placeholder')}
          value={query}
          onChange={handleChange}
          autoFocus
        />
        {query && (
          <button className={styles.clearBtn} onClick={clear}>✕</button>
        )}
      </div>

      {loading && <p className={styles.hint}>{t('search.searching')}</p>}

      <div className={styles.resultsList}>
        {results.map((item) => (
          <div key={item.id} className={styles.resultItem}>
            <div className={styles.resultInfo}>
              <span className={styles.resultName}>{item.name}</span>
              <span className={styles.resultMeta}>{item.sku} · {t('search.stock', { count: item.stock })}</span>
            </div>
            <span className={styles.resultPrice}>{item.price.toFixed(2)}</span>
            <button
              className={styles.addBtn}
              onClick={() => onAddItem(item)}
              disabled={item.stock < 1}
            >
              +
            </button>
          </div>
        ))}
        {!loading && query && results.length === 0 && (
          <p className={styles.hint}>{t('search.noResults')}</p>
        )}
      </div>
    </div>
  )
}
