import { api } from './client'

export const searchProducts = (params = {}) => {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
  ).toString()
  return api.get(`/catalog/products${qs ? '?' + qs : ''}`)
}

export const getProduct = (id) => api.get(`/catalog/products/${id}`)
export const createProduct = (data) => api.post('/catalog/products', data)
export const updateProduct = (id, data) => api.patch(`/catalog/products/${id}`, data)
export const deleteProduct = (id) => api.delete(`/catalog/products/${id}`)
export const adjustStock = (id, delta, reason = '') =>
  api.post(`/catalog/products/${id}/stock`, { delta, reason })
export const getCategories = () => api.get('/catalog/categories')
