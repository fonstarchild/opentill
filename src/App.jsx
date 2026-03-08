import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import useConfigStore from './store/configStore'
import Sidebar from './components/shared/Sidebar'
import POSPage from './pages/POSPage'
import CatalogPage from './pages/CatalogPage'
import OrdersPage from './pages/OrdersPage'
import SettingsPage from './pages/SettingsPage'
import MetricsPage from './pages/MetricsPage'
import styles from './App.module.css'

const PAGE_COMPONENTS = {
  pos:      { icon: '🖥',  component: POSPage },
  catalog:  { icon: '📦',  component: CatalogPage },
  orders:   { icon: '🧾',  component: OrdersPage },
  metrics:  { icon: '📊',  component: MetricsPage },
  settings: { icon: '⚙️',  component: SettingsPage },
}

export default function App() {
  const [page, setPage] = useState('pos')
  const { fetchConfig } = useConfigStore()
  const { t } = useTranslation()

  useEffect(() => { fetchConfig() }, [fetchConfig])

  const pages = {
    pos:      { ...PAGE_COMPONENTS.pos,      label: t('nav.pos') },
    catalog:  { ...PAGE_COMPONENTS.catalog,  label: t('nav.catalog') },
    orders:   { ...PAGE_COMPONENTS.orders,   label: t('nav.orders') },
    metrics:  { ...PAGE_COMPONENTS.metrics,  label: t('nav.metrics') },
    settings: { ...PAGE_COMPONENTS.settings, label: t('nav.settings') },
  }

  const Page = pages[page]?.component ?? POSPage

  return (
    <div className={styles.shell}>
      <Sidebar pages={pages} current={page} onChange={setPage} />
      <main className={styles.main}>
        <Page />
      </main>
    </div>
  )
}
