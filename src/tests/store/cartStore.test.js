import { describe, it, expect, beforeEach } from 'vitest'
import { act } from '@testing-library/react'
import useCartStore from '../../store/cartStore'

const sampleProduct = {
  id: 1,
  name: 'Test Product',
  price: 9.99,
  stock: 10,
  sku: 'TEST-001',
  tax_rate: 0.21,
}

describe('cartStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    act(() => {
      useCartStore.getState().clear()
    })
  })

  describe('addItem', () => {
    it('adds a new product to cart', () => {
      act(() => {
        useCartStore.getState().addItem(sampleProduct)
      })
      const items = useCartStore.getState().items
      expect(items).toHaveLength(1)
      expect(items[0].id).toBe(1)
      expect(items[0].quantity).toBe(1)
    })

    it('increments quantity for existing product', () => {
      act(() => {
        useCartStore.getState().addItem(sampleProduct)
        useCartStore.getState().addItem(sampleProduct)
      })
      const items = useCartStore.getState().items
      expect(items).toHaveLength(1)
      expect(items[0].quantity).toBe(2)
    })

    it('does not exceed stock limit', () => {
      const limitedProduct = { ...sampleProduct, stock: 2 }
      act(() => {
        for (let i = 0; i < 5; i++) {
          useCartStore.getState().addItem(limitedProduct)
        }
      })
      expect(useCartStore.getState().items[0].quantity).toBe(2)
    })

    it('adds multiple different products', () => {
      const product2 = { ...sampleProduct, id: 2, name: 'Product 2' }
      act(() => {
        useCartStore.getState().addItem(sampleProduct)
        useCartStore.getState().addItem(product2)
      })
      expect(useCartStore.getState().items).toHaveLength(2)
    })
  })

  describe('removeItem', () => {
    it('removes product from cart', () => {
      act(() => {
        useCartStore.getState().addItem(sampleProduct)
        useCartStore.getState().removeItem(sampleProduct.id)
      })
      expect(useCartStore.getState().items).toHaveLength(0)
    })

    it('does not affect other items', () => {
      const product2 = { ...sampleProduct, id: 2 }
      act(() => {
        useCartStore.getState().addItem(sampleProduct)
        useCartStore.getState().addItem(product2)
        useCartStore.getState().removeItem(sampleProduct.id)
      })
      expect(useCartStore.getState().items).toHaveLength(1)
      expect(useCartStore.getState().items[0].id).toBe(2)
    })
  })

  describe('setQuantity', () => {
    it('sets quantity for product', () => {
      act(() => {
        useCartStore.getState().addItem(sampleProduct)
        useCartStore.getState().setQuantity(sampleProduct.id, 5)
      })
      expect(useCartStore.getState().items[0].quantity).toBe(5)
    })

    it('removes item when quantity set to 0', () => {
      act(() => {
        useCartStore.getState().addItem(sampleProduct)
        useCartStore.getState().setQuantity(sampleProduct.id, 0)
      })
      expect(useCartStore.getState().items).toHaveLength(0)
    })

    it('caps quantity at stock level', () => {
      act(() => {
        useCartStore.getState().addItem(sampleProduct)
        useCartStore.getState().setQuantity(sampleProduct.id, 999)
      })
      expect(useCartStore.getState().items[0].quantity).toBe(sampleProduct.stock)
    })
  })

  describe('clear', () => {
    it('empties the cart', () => {
      act(() => {
        useCartStore.getState().addItem(sampleProduct)
        useCartStore.getState().clear()
      })
      expect(useCartStore.getState().items).toHaveLength(0)
    })
  })

  describe('subtotal', () => {
    it('calculates subtotal for single item', () => {
      act(() => {
        useCartStore.getState().addItem(sampleProduct)
        useCartStore.getState().setQuantity(sampleProduct.id, 3)
      })
      expect(useCartStore.getState().subtotal()).toBeCloseTo(29.97)
    })

    it('returns 0 for empty cart', () => {
      expect(useCartStore.getState().subtotal()).toBe(0)
    })
  })
})
