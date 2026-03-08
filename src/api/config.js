import { api } from './client'

export const getConfig = () => api.get('/config/')
export const updateConfig = (data) => api.put('/config/', data)
export const updatePaymentMethods = (active, configs) =>
  api.patch('/config/payment-methods', { active, configs })
