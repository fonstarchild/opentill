import styles from './Sidebar.module.css'

export default function Sidebar({ pages, current, onChange }) {
  return (
    <nav className={styles.sidebar}>
      <div className={styles.logo}>
        <span className={styles.logoIcon}>⊞</span>
        <span className={styles.logoText}>Opentill</span>
      </div>

      <ul className={styles.navList}>
        {Object.entries(pages).map(([key, { label, icon }]) => (
          <li key={key}>
            <button
              className={`${styles.navItem} ${current === key ? styles.navItemActive : ''}`}
              onClick={() => onChange(key)}
            >
              <span className={styles.navIcon}>{icon}</span>
              <span>{label}</span>
            </button>
          </li>
        ))}
      </ul>

      <div className={styles.sidebarFooter}>
        <span className={styles.version}>v0.1.0</span>
      </div>
    </nav>
  )
}
