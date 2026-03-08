import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { listOrders, voidOrder } from '../api/orders'
import styles from './Pages.module.css'
import tableStyles from './Table.module.css'

export default function OrdersPage() {
  const { t } = useTranslation()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const data = await listOrders({ page_size: 100 })
      setOrders(Array.isArray(data) ? data : data.results ?? data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleVoid = async (order) => {
    if (!confirm(t('orders.voidConfirm', { reference: order.reference }))) return
    try {
      const updated = await voidOrder(order.id)
      setOrders((prev) => prev.map((o) => o.id === updated.id ? updated : o))
    } catch (e) { alert(e.message) }
  }

  return (
    <div className={styles.pageWrapper}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>{t('orders.title')}</h1>
        <button className={tableStyles.cancelBtn} onClick={load}>{t('orders.refresh')}</button>
      </div>

      <div className={tableStyles.tableWrapper}>
        <table className={tableStyles.table}>
          <thead>
            <tr>
              <th>{t('orders.colReference')}</th>
              <th>{t('orders.colDate')}</th>
              <th>{t('orders.colTotal')}</th>
              <th>{t('orders.colPayment')}</th>
              <th>{t('orders.colStatus')}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className={tableStyles.empty}>{t('orders.loading')}</td></tr>
            ) : orders.length === 0 ? (
              <tr><td colSpan={6} className={tableStyles.empty}>{t('orders.noOrders')}</td></tr>
            ) : orders.map((o) => (
              <tr key={o.id}>
                <td className={tableStyles.mono}>{o.reference}</td>
                <td>{new Date(o.created_at).toLocaleString()}</td>
                <td>{parseFloat(o.total).toFixed(2)}</td>
                <td>{o.payment_method}</td>
                <td>
                  <span className={`${tableStyles.badge} ${o.status === 'COMPLETED' ? tableStyles.badgeGreen : o.status === 'VOID' ? tableStyles.badgeRed : tableStyles.badgeGray}`}>
                    {o.status}
                  </span>
                </td>
                <td>
                  {o.status === 'COMPLETED' && (
                    <button className={tableStyles.editBtn} onClick={() => handleVoid(o)}>{t('orders.void')}</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
