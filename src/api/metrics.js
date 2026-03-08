import { api } from './client'

export const getMetrics = (year, month) =>
  api.get(`/orders/metrics?year=${year}&month=${month}`)
