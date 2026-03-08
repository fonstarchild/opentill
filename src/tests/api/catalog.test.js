import { describe, it, expect, vi, beforeEach } from 'vitest'
import { searchProducts, getProduct, createProduct, adjustStock } from '../../api/catalog'

// Mock the api client
vi.mock('../../api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

import { api } from '../../api/client'

const sampleProduct = {
  id: 1,
  name: 'Widget',
  sku: 'WIDGET-001',
  price: 9.99,
  stock: 10,
}

describe('catalog API client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('searchProducts', () => {
    it('calls GET /catalog/products', async () => {
      api.get.mockResolvedValue([sampleProduct])
      const result = await searchProducts()
      expect(api.get).toHaveBeenCalledWith('/catalog/products')
      expect(result).toEqual([sampleProduct])
    })

    it('passes search params as query string', async () => {
      api.get.mockResolvedValue([])
      await searchProducts({ search: 'widget', category: 'Tools' })
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining('search=widget')
      )
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining('category=Tools')
      )
    })

    it('omits undefined params', async () => {
      api.get.mockResolvedValue([])
      await searchProducts({ search: undefined })
      expect(api.get).toHaveBeenCalledWith('/catalog/products')
    })
  })

  describe('getProduct', () => {
    it('calls GET /catalog/products/:id', async () => {
      api.get.mockResolvedValue(sampleProduct)
      const result = await getProduct(1)
      expect(api.get).toHaveBeenCalledWith('/catalog/products/1')
      expect(result).toEqual(sampleProduct)
    })
  })

  describe('createProduct', () => {
    it('calls POST /catalog/products', async () => {
      api.post.mockResolvedValue({ ...sampleProduct, id: 2 })
      await createProduct({ name: 'New Product', sku: 'NEW-001', price: 5.0 })
      expect(api.post).toHaveBeenCalledWith(
        '/catalog/products',
        expect.objectContaining({ name: 'New Product' })
      )
    })
  })

  describe('adjustStock', () => {
    it('calls POST /catalog/products/:id/stock with delta', async () => {
      api.post.mockResolvedValue({ ...sampleProduct, stock: 15 })
      await adjustStock(1, 5)
      expect(api.post).toHaveBeenCalledWith(
        '/catalog/products/1/stock',
        { delta: 5, reason: '' }
      )
    })
  })
})
