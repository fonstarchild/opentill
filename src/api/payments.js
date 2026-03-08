import { api } from './client'

export const listProviders = () => api.get('/payments/providers')
export const charge = (data) => api.post('/payments/charge', data)
