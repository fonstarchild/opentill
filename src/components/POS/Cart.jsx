import { useTranslation } from 'react-i18next'
import useCartStore from '../../store/cartStore'
import useConfigStore from '../../store/configStore'
import styles from './POS.module.css'

export default function Cart({ paymentMethods, onCheckout }) {
  const { items, setQuantity, removeItem } = useCartStore()
  const { config } = useConfigStore()
  const { t } = useTranslation()
  const currency = config?.currency ?? 'EUR'
  const subtotal = items.reduce((s, i) => s + i.price * i.quantity, 0)

  return (
    <div className={styles.cart}>
      <h2 className={styles.panelTitle}>
        {t('cart.title')} {items.length > 0 && <span className={styles.badge}>{items.length}</span>}
      </h2>

      <div className={styles.cartItems}>
        {items.length === 0 ? (
          <p className={styles.hint}>{t('cart.empty')}</p>
        ) : (
          items.map((item) => (
            <div key={item.id} className={styles.cartItem}>
              <div className={styles.cartItemInfo}>
                <span className={styles.cartItemName}>{item.name}</span>
                <span className={styles.cartItemSubtotal}>
                  {(item.price * item.quantity).toFixed(2)} {currency}
                </span>
              </div>
              <div className={styles.qtyControls}>
                <button onClick={() => setQuantity(item.id, item.quantity - 1)}>−</button>
                <span>{item.quantity}</span>
                <button
                  onClick={() => setQuantity(item.id, item.quantity + 1)}
                  disabled={item.quantity >= item.stock}
                >
                  +
                </button>
              </div>
              <button className={styles.removeBtn} onClick={() => removeItem(item.id)}>✕</button>
            </div>
          ))
        )}
      </div>

      <div className={styles.cartTotal}>
        <span>{t('cart.total')}</span>
        <span className={styles.totalAmount}>{subtotal.toFixed(2)} {currency}</span>
      </div>

      <button
        className={styles.checkoutBtn}
        onClick={onCheckout}
        disabled={items.length === 0}
      >
        {t('cart.charge', { amount: subtotal.toFixed(2), currency })}
      </button>
    </div>
  )
}
