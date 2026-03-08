import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import useCartStore from '../../store/cartStore'
import { createOrder } from '../../api/orders'
import styles from './POS.module.css'

export default function CheckoutDialog({ paymentMethods, config, onSuccess, onClose }) {
  const { items, clear } = useCartStore()
  const { t } = useTranslation()
  const subtotal = items.reduce((s, i) => s + i.price * i.quantity, 0)
  const currency = config?.currency ?? 'EUR'

  const [method, setMethod] = useState(paymentMethods[0]?.id ?? 'CASH')
  const [discount, setDiscount] = useState('')
  const [amountReceived, setAmountReceived] = useState('')
  const [customerName, setCustomerName] = useState('')
  const [customerEmail, setCustomerEmail] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const discountVal = Math.min(parseFloat(discount) || 0, subtotal)
  const total = Math.max(subtotal - discountVal, 0)
  const received = parseFloat(amountReceived) || 0
  const change = method === 'CASH' && received > 0 ? Math.max(received - total, 0) : null

  const handleConfirm = async () => {
    setLoading(true)
    setError(null)
    try {
      const order = await createOrder({
        items: items.map((i) => ({ product_id: i.id, quantity: i.quantity })),
        payment_method: method,
        discount_amount: discountVal,
        amount_received: method === 'CASH' ? received : 0,
        notes,
        customer_name: customerName,
        customer_email: customerEmail,
      })
      clear()
      onSuccess(order, { paymentMethod: method, amountReceived: received, discountAmount: discountVal })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.dialogOverlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.dialog}>
        <div className={styles.dialogHeader}>
          <h3>{t('checkout.title')}</h3>
          <button className={styles.dialogClose} onClick={onClose}>✕</button>
        </div>

        <div className={styles.dialogBody}>
          <label className={styles.fieldLabel}>{t('checkout.paymentMethod')}</label>
          <div className={styles.methodList}>
            {paymentMethods.map((m) => (
              <button
                key={m.id}
                className={`${styles.methodBtn} ${method === m.id ? styles.methodBtnActive : ''}`}
                style={{ '--method-color': m.color ?? '#6366f1' }}
                onClick={() => setMethod(m.id)}
              >
                {m.name}
              </button>
            ))}
          </div>

          <label className={styles.fieldLabel}>{t('checkout.discount', { currency })}</label>
          <input
            className={styles.fieldInput}
            type="number" min="0" step="0.01"
            placeholder="0.00"
            value={discount}
            onChange={(e) => setDiscount(e.target.value)}
          />

          <div className={styles.totalBox}>
            <span>{t('checkout.totalToCharge')}</span>
            <span className={styles.totalAmount}>{total.toFixed(2)} {currency}</span>
          </div>

          {method === 'CASH' && (
            <>
              <label className={styles.fieldLabel}>{t('checkout.amountReceived', { currency })}</label>
              <input
                className={styles.fieldInput}
                type="number" min="0" step="0.01"
                placeholder="0.00"
                value={amountReceived}
                onChange={(e) => setAmountReceived(e.target.value)}
              />
              {change !== null && received > 0 && (
                <div className={styles.changeBox}>
                  {t('checkout.change')}<strong>{change.toFixed(2)} {currency}</strong>
                </div>
              )}
            </>
          )}

          <label className={styles.fieldLabel}>{t('checkout.customerName')}</label>
          <input
            className={styles.fieldInput}
            placeholder={t('checkout.namePlaceholder')}
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
          />
          <label className={styles.fieldLabel}>{t('checkout.customerEmail')}</label>
          <input
            className={styles.fieldInput}
            type="email"
            placeholder="email@example.com"
            value={customerEmail}
            onChange={(e) => setCustomerEmail(e.target.value)}
          />

          <label className={styles.fieldLabel}>{t('checkout.notes')}</label>
          <textarea
            className={styles.fieldInput}
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />

          {error && <div className={styles.errorMsg}>{error}</div>}
        </div>

        <div className={styles.dialogActions}>
          <button className={styles.cancelBtn} onClick={onClose} disabled={loading}>
            {t('checkout.cancel')}
          </button>
          <button className={styles.confirmBtn} onClick={handleConfirm} disabled={loading}>
            {loading ? t('checkout.processing') : t('checkout.chargeBtn', { amount: total.toFixed(2), currency })}
          </button>
        </div>
      </div>
    </div>
  )
}
