import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  ResponsiveContainer,
  BarChart, Bar,
  LineChart, Line,
  PieChart, Pie, Cell, Tooltip as PieTooltip, Legend as PieLegend,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts'
import { getMetrics } from '../api/metrics'
import styles from './Metrics.module.css'

const MONTH_NAMES_EN = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

const PAYMENT_COLORS = {
  CASH:   '#10b981',
  TPV:    '#7c3aed',
  BIZUM:  '#06b6d4',
  STRIPE: '#6366f1',
  SUMUP:  '#f59e0b',
  PAYPAL: '#3b82f6',
  REDSYS: '#ef4444',
  SQUARE: '#8b5cf6',
}
const DEFAULT_COLOR = '#64748b'

function useMetrics(year, month) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    getMetrics(year, month)
      .then(setData)
      .catch(e => setError(e?.message ?? 'Error'))
      .finally(() => setLoading(false))
  }, [year, month])

  return { data, loading, error }
}

function NoData({ label }) {
  return <div className={styles.noData}>{label}</div>
}

export default function MetricsPage() {
  const { t } = useTranslation()
  const currentYear = new Date().getFullYear()
  const currentMonth = new Date().getMonth() + 1

  const [year, setYear] = useState(currentYear)
  const [month, setMonth] = useState(currentMonth)
  const { data, loading, error } = useMetrics(year, month)

  const chartColor = '#6366f1'   // var(--accent)
  const chartMuted = '#64748b'   // var(--text-muted)

  // Build full 12-month array with zeros for missing months
  const monthlyData = Array.from({ length: 12 }, (_, i) => {
    const m = i + 1
    const found = data?.monthly?.find(r => r.month === m)
    return { name: MONTH_NAMES_EN[i], revenue: found?.revenue ?? 0, orders: found?.orders ?? 0 }
  })

  // Daily data for selected month (sparse, only days with sales)
  const dailyData = (data?.daily ?? []).map(r => ({ name: String(r.day), revenue: r.revenue, orders: r.orders }))

  const byPayment = (data?.by_payment ?? []).map(r => ({
    name: r.method,
    value: r.revenue,
    color: PAYMENT_COLORS[r.method] ?? DEFAULT_COLOR,
  }))

  const topProducts = (data?.top_products ?? []).map(r => ({
    name: r.product_name.length > 20 ? r.product_name.slice(0, 18) + '…' : r.product_name,
    revenue: r.revenue,
    units: r.units,
  }))

  const bestMonthName = data?.kpi?.best_month != null
    ? MONTH_NAMES_EN[data.kpi.best_month - 1]
    : '—'

  const noData = t('metrics.noData')
  const loadingLabel = t('metrics.loading')

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <h1 className={styles.title}>{t('metrics.title')}</h1>
        <div className={styles.yearNav}>
          <button className={styles.yearBtn} onClick={() => setYear(y => y - 1)}>←</button>
          <span className={styles.yearLabel}>{year}</span>
          <button className={styles.yearBtn} onClick={() => setYear(y => y + 1)}>→</button>
        </div>
        <select
          className={styles.monthSelect}
          value={month}
          onChange={e => setMonth(Number(e.target.value))}
        >
          {MONTH_NAMES_EN.map((name, i) => (
            <option key={i + 1} value={i + 1}>{name}</option>
          ))}
        </select>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {/* KPI Cards */}
      <div className={styles.kpiRow}>
        <div className={styles.kpiCard}>
          <span className={styles.kpiLabel}>{t('metrics.totalRevenue')}</span>
          <span className={`${styles.kpiValue} ${styles.kpiAccent}`}>
            {loading ? '…' : (data?.kpi?.total_revenue ?? 0).toFixed(2)}
          </span>
        </div>
        <div className={styles.kpiCard}>
          <span className={styles.kpiLabel}>{t('metrics.orderCount')}</span>
          <span className={styles.kpiValue}>
            {loading ? '…' : (data?.kpi?.order_count ?? 0)}
          </span>
        </div>
        <div className={styles.kpiCard}>
          <span className={styles.kpiLabel}>{t('metrics.avgTicket')}</span>
          <span className={styles.kpiValue}>
            {loading ? '…' : (data?.kpi?.avg_ticket ?? 0).toFixed(2)}
          </span>
        </div>
        <div className={styles.kpiCard}>
          <span className={styles.kpiLabel}>{t('metrics.bestMonth')}</span>
          <span className={`${styles.kpiValue} ${styles.kpiAccent}`}>
            {loading ? '…' : bestMonthName}
          </span>
        </div>
      </div>

      {/* Charts */}
      <div className={styles.chartsGrid}>

        {/* Daily Bar Chart */}
        <div className={styles.chartCard}>
          <div className={styles.chartTitle}>{t('metrics.dailySales')}</div>
          {loading
            ? <div className={styles.noData}>{loadingLabel}</div>
            : dailyData.length === 0
              ? <NoData label={noData} />
              : (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={dailyData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="name" tick={{ fill: chartMuted, fontSize: 11 }} />
                    <YAxis tick={{ fill: chartMuted, fontSize: 11 }} width={40} />
                    <Tooltip
                      contentStyle={{ background: '#1a1d27', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 12 }}
                      labelStyle={{ color: '#e2e8f0' }}
                    />
                    <Bar dataKey="revenue" fill={chartColor} radius={[3, 3, 0, 0]} name={t('metrics.revenue')} />
                  </BarChart>
                </ResponsiveContainer>
              )
          }
        </div>

        {/* Monthly Line Chart */}
        <div className={styles.chartCard}>
          <div className={styles.chartTitle}>{t('metrics.monthlySales')}</div>
          {loading
            ? <div className={styles.noData}>{loadingLabel}</div>
            : monthlyData.every(d => d.revenue === 0)
              ? <NoData label={noData} />
              : (
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={monthlyData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="name" tick={{ fill: chartMuted, fontSize: 11 }} />
                    <YAxis tick={{ fill: chartMuted, fontSize: 11 }} width={40} />
                    <Tooltip
                      contentStyle={{ background: '#1a1d27', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 12 }}
                      labelStyle={{ color: '#e2e8f0' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="revenue"
                      stroke={chartColor}
                      strokeWidth={2}
                      dot={{ r: 3, fill: chartColor }}
                      name={t('metrics.revenue')}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )
          }
        </div>

        {/* By Payment Pie Chart */}
        <div className={styles.chartCard}>
          <div className={styles.chartTitle}>{t('metrics.byPayment')}</div>
          {loading
            ? <div className={styles.noData}>{loadingLabel}</div>
            : byPayment.length === 0
              ? <NoData label={noData} />
              : (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={byPayment}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={70}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {byPayment.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <PieTooltip
                      contentStyle={{ background: '#1a1d27', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 12 }}
                    />
                    <PieLegend wrapperStyle={{ fontSize: 11, color: chartMuted }} />
                  </PieChart>
                </ResponsiveContainer>
              )
          }
        </div>

        {/* Top Products Horizontal Bar Chart */}
        <div className={styles.chartCard}>
          <div className={styles.chartTitle}>{t('metrics.topProducts')}</div>
          {loading
            ? <div className={styles.noData}>{loadingLabel}</div>
            : topProducts.length === 0
              ? <NoData label={noData} />
              : (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart
                    data={topProducts}
                    layout="vertical"
                    margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis type="number" tick={{ fill: chartMuted, fontSize: 11 }} />
                    <YAxis
                      type="category"
                      dataKey="name"
                      tick={{ fill: chartMuted, fontSize: 11 }}
                      width={90}
                    />
                    <Tooltip
                      contentStyle={{ background: '#1a1d27', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 12 }}
                      labelStyle={{ color: '#e2e8f0' }}
                    />
                    <Legend wrapperStyle={{ fontSize: 11, color: chartMuted }} />
                    <Bar dataKey="revenue" fill={chartColor} radius={[0, 3, 3, 0]} name={t('metrics.revenue')} />
                    <Bar dataKey="units" fill="#10b981" radius={[0, 3, 3, 0]} name={t('metrics.units')} />
                  </BarChart>
                </ResponsiveContainer>
              )
          }
        </div>

      </div>
    </div>
  )
}
