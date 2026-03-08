import { api } from './client'

export const createOrder = (data) => api.post('/orders/', data)
export const listOrders = (params = {}) => {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
  ).toString()
  return api.get(`/orders/${qs ? '?' + qs : ''}`)
}
export const getOrder = (id) => api.get(`/orders/${id}`)
export const voidOrder = (id) => api.post(`/orders/${id}/void`, {})
