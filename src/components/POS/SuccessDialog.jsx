import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { buildReceiptHtml, printReceipt } from '../Ticket/TicketPrint'
import styles from './POS.module.css'

export default function SuccessDialog({ order, paymentInfo, config, onClose }) {
  const { t } = useTranslation()
  const [previewOpen, setPreviewOpen] = useState(false)
  const currency = config?.currency ?? 'EUR'

  const ticketParams = {
    order,
    config,
    paymentMethod: paymentInfo?.paymentMethod ?? 'CASH',
    amountReceived: paymentInfo?.amountReceived ?? 0,
    discountAmount: paymentInfo?.discountAmount ?? 0,
    labels: {
      subtotal: t('receipt.subtotal'),
      discount: t('receipt.discount'),
      total:    'TOTAL',
      payment:  t('receipt.payment'),
      received: t('receipt.received'),
      change:   t('receipt.change'),
      vatTitle: t('receipt.vatBreakdownTitle'),
      vatBase:  t('receipt.vatBase'),
      vatQuota: t('receipt.vatQuota'),
      vatTotal: t('receipt.vatTotal'),
    },
  }

  const handlePrint = () => printReceipt(ticketParams)

  return (
    <div className={styles.dialogOverlay}>
      <div className={styles.dialog}>
        <div className={styles.dialogHeader}>
          <h3 style={{ color: '#10b981' }}>{t('success.title')}</h3>
          <button className={styles.dialogClose} onClick={onClose}>✕</button>
        </div>

        <div className={styles.dialogBody}>
          <p dangerouslySetInnerHTML={{ __html: t('success.orderCreated', { reference: order.reference }) }} />
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            {t('success.total')}<strong>{order.total} {currency}</strong>
          </p>
          {order.change_given > 0 && (
            <div className={styles.changeBox}>
              {t('success.changeGiven')}<strong>{order.change_given.toFixed(2)} {currency}</strong>
            </div>
          )}
          <div style={{ marginTop: '0.5rem' }}>
            {(order.items ?? []).map((item) => (
              <p key={item.id} style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {item.quantity}× {item.product_name} — {item.total_price} {currency}
              </p>
            ))}
          </div>
        </div>

        <div className={styles.dialogActions}>
          <button className={styles.cancelBtn} onClick={onClose}>{t('success.close')}</button>
          <button className={styles.cancelBtn} onClick={() => setPreviewOpen(true)}>{t('success.preview')}</button>
          <button className={styles.confirmBtn} onClick={handlePrint}>{t('success.printReceipt')}</button>
        </div>
      </div>

      {previewOpen && (
        <div className={styles.dialogOverlay} onClick={() => setPreviewOpen(false)}>
          <div className={styles.dialog} onClick={(e) => e.stopPropagation()}>
            <div className={styles.dialogHeader}>
              <h3>{t('success.receiptPreview')}</h3>
              <button className={styles.dialogClose} onClick={() => setPreviewOpen(false)}>✕</button>
            </div>
            <div style={{ padding: '1rem', background: '#f5f5f5', display: 'flex', justifyContent: 'center', maxHeight: '60vh', overflowY: 'auto' }}>
              <iframe
                srcDoc={buildReceiptHtml(ticketParams)}
                title={t('success.receiptPreview')}
                style={{ border: 'none', width: '320px', minHeight: '500px', background: '#fff', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}
              />
            </div>
            <div className={styles.dialogActions}>
              <button className={styles.cancelBtn} onClick={() => setPreviewOpen(false)}>{t('success.close')}</button>
              <button className={styles.confirmBtn} onClick={handlePrint}>{t('success.print')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
