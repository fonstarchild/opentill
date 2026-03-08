import { create } from 'zustand'
import { getConfig } from '../api/config'

const useConfigStore = create((set) => ({
  config: null,
  loading: false,

  fetchConfig: async () => {
    set({ loading: true })
    try {
      const config = await getConfig()
      set({ config })
    } catch (e) {
      console.error('Failed to load config:', e)
    } finally {
      set({ loading: false })
    }
  },

  setConfig: (config) => set({ config }),
}))

export default useConfigStore
