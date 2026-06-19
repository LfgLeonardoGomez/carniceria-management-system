import { create } from 'zustand'
import type { Producto } from '@/shared/types/producto'

export interface CartItem {
  /** Producto asociado al ítem. */
  producto: Producto
  /** Peso en kilogramos (cantidad para productos pesados). */
  cantidadKg: number
  /** Subtotal calculado con precisión decimal. */
  subtotal: string
}

interface CartState {
  items: CartItem[]
  addItem: (item: CartItem) => void
  removeItem: (productoId: string) => void
  clearCart: () => void
}

export const useCartStore = create<CartState>((set) => ({
  items: [],
  addItem: (item) =>
    set((state) => ({
      items: [...state.items, item],
    })),
  removeItem: (productoId) =>
    set((state) => ({
      items: state.items.filter((i) => i.producto.id !== productoId),
    })),
  clearCart: () => set({ items: [] }),
}))
