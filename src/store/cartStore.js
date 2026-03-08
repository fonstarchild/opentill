import { create } from 'zustand'

const useCartStore = create((set, get) => ({
  items: [],

  addItem: (product) => {
    set((state) => {
      const existing = state.items.find((i) => i.id === product.id)
      if (existing) {
        if (existing.quantity >= existing.stock) return state
        return {
          items: state.items.map((i) =>
            i.id === product.id ? { ...i, quantity: i.quantity + 1 } : i
          ),
        }
      }
      return { items: [...state.items, { ...product, quantity: 1 }] }
    })
  },

  setQuantity: (id, quantity) => {
    if (quantity < 1) {
      set((state) => ({ items: state.items.filter((i) => i.id !== id) }))
    } else {
      set((state) => ({
        items: state.items.map((i) =>
          i.id === id ? { ...i, quantity: Math.min(quantity, i.stock) } : i
        ),
      }))
    }
  },

  removeItem: (id) => set((state) => ({ items: state.items.filter((i) => i.id !== id) })),

  clear: () => set({ items: [] }),

  subtotal: () => get().items.reduce((s, i) => s + i.price * i.quantity, 0),
}))

export default useCartStore
