import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import useCartStore from '../store/cartStore'
import useConfigStore from '../store/configStore'
import SearchPanel from '../components/POS/SearchPanel'
import ScannerPanel from '../components/POS/ScannerPanel'
import Cart from '../components/POS/Cart'
import CheckoutDialog from '../components/POS/CheckoutDialog'
import SuccessDialog from '../components/POS/SuccessDialog'
import styles from '../components/POS/POS.module.css'
import appStyles from './Pages.module.css'

export default function POSPage() {
  const { addItem } = useCartStore()
  const { config } = useConfigStore()
  const { t } = useTranslation()

  const [scannerMode, setScannerMode] = useState(false)
  const [checkoutOpen, setCheckoutOpen] = useState(false)
  const [successData, setSuccessData] = useState(null)

  const activeMethods = (config?.active_payment_methods ?? ['CASH']).map((id) => ({
    id,
    name: id.charAt(0) + id.slice(1).toLowerCase().replace('_', ' '),
    color: {
      CASH: '#10b981',
      TPV: '#7c3aed',
      BIZUM: '#06b6d4',
      BANK_TRANSFER: '#f59e0b',
      STRIPE_TERMINAL: '#6366f1',
      SUMUP: '#0070e0',
    }[id] ?? '#6366f1',
  }))

  const handleSuccess = (order, paymentInfo) => {
    setCheckoutOpen(false)
    setSuccessData({ order, paymentInfo })
  }

  return (
    <div className={appStyles.pageWrapper}>
      <div className={appStyles.pageHeader}>
        <h1 className={appStyles.pageTitle}>{t('pos.title')}</h1>
        <label className={appStyles.toggle}>
          <input
            type="checkbox"
            checked={scannerMode}
            onChange={(e) => setScannerMode(e.target.checked)}
          />
          <span>{t('pos.scannerMode')}</span>
        </label>
      </div>

      <div className={styles.posLayout}>
        <div style={{ overflow: 'hidden' }}>
          {scannerMode
            ? <ScannerPanel onAddItem={addItem} />
            : <SearchPanel onAddItem={addItem} />}
        </div>

        <Cart
          paymentMethods={activeMethods}
          onCheckout={() => setCheckoutOpen(true)}
        />
      </div>

      {checkoutOpen && (
        <CheckoutDialog
          paymentMethods={activeMethods}
          config={config}
          onSuccess={handleSuccess}
          onClose={() => setCheckoutOpen(false)}
        />
      )}

      {successData && (
        <SuccessDialog
          order={successData.order}
          paymentInfo={successData.paymentInfo}
          config={config}
          onClose={() => setSuccessData(null)}
        />
      )}
    </div>
  )
}
