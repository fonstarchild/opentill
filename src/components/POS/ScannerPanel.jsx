import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { searchProducts } from '../../api/catalog'
import styles from './POS.module.css'

export default function ScannerPanel({ onAddItem }) {
  const { t } = useTranslation()
  const [code, setCode] = useState('')
  const [status, setStatus] = useState(null) // null | 'ok' | 'error'
  const [statusMsg, setStatusMsg] = useState('')
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    const interval = setInterval(() => {
      if (document.activeElement !== inputRef.current) {
        inputRef.current?.focus()
      }
    }, 300)
    inputRef.current?.focus()
    return () => clearInterval(interval)
  }, [])

  const handleKeyDown = async (e) => {
    if (e.key !== 'Enter') return
    const raw = code.trim()
    if (!raw) return
    setCode('')
    setLoading(true)
    setStatus(null)

    try {
      let found = null

      const bySku = await searchProducts({ sku: raw, page_size: 1 })
      const skuItems = Array.isArray(bySku) ? bySku : bySku.results ?? bySku
      if (skuItems[0]?.sku?.toLowerCase() === raw.toLowerCase()) {
        found = skuItems[0]
      }

      if (!found) {
        const byBarcode = await searchProducts({ barcode: raw, page_size: 1 })
        const bcItems = Array.isArray(byBarcode) ? byBarcode : byBarcode.results ?? byBarcode
        if (bcItems[0]?.barcode === raw) found = bcItems[0]
      }

      if (found) {
        onAddItem(found)
        setStatus('ok')
        setStatusMsg(`✓ ${found.name} — ${found.price.toFixed(2)}`)
        setTimeout(() => setStatus(null), 2500)
      } else {
        setStatus('error')
        setStatusMsg(t('scanner.notFound', { code: raw }))
        setTimeout(() => setStatus(null), 3000)
      }
    } catch {
      setStatus('error')
      setStatusMsg(t('scanner.lookupError'))
      setTimeout(() => setStatus(null), 3000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.panel}>
      <div className={styles.scannerHeader}>
        <h2 className={styles.panelTitle}>{t('scanner.title')}</h2>
        <span className={styles.activeBadge}>{t('scanner.active')}</span>
      </div>

      <p className={styles.hint}>{t('scanner.hint')}</p>

      <input
        ref={inputRef}
        className={styles.searchInput}
        placeholder={t('scanner.placeholder')}
        value={code}
        onChange={(e) => setCode(e.target.value)}
        onKeyDown={handleKeyDown}
        autoComplete="off"
      />

      {loading && <p className={styles.hint}>{t('scanner.lookingUp')}</p>}

      {status === 'ok' && (
        <div className={`${styles.statusMsg} ${styles.statusOk}`}>{statusMsg}</div>
      )}
      {status === 'error' && (
        <div className={`${styles.statusMsg} ${styles.statusError}`}>{statusMsg}</div>
      )}

      <p className={styles.hintSmall}>{t('scanner.autoFocusHint')}</p>
    </div>
  )
}
