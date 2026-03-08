import { describe, it, expect } from 'vitest'
import { buildReceiptHtml } from '../../components/Ticket/TicketPrint'

const baseOrder = {
  reference: 'OT-20240101-0001',
  total: 19.99,
  items: [
    {
      product_name: 'Widget',
      quantity: 2,
      unit_price: 9.99,
      tax_rate: 0.21,
    },
    {
      product_name: 'Gadget',
      quantity: 1,
      unit_price: 0.01,
      tax_rate: 0.10,
    },
  ],
}

const baseConfig = {
  shop: {
    name: 'Test Shop',
    address: '123 Main St',
    phone: '+1 234 567 890',
    tax_id: 'B12345678',
    receipt_footer: 'Thank you!',
  },
  currency: 'EUR',
  locale: 'en-US',
  receipt: {
    paper_width_mm: 80,
    show_vat_breakdown: true,
    logo_url: '',
  },
}

describe('buildReceiptHtml', () => {
  it('returns a string', () => {
    const html = buildReceiptHtml({ order: baseOrder, config: baseConfig })
    expect(typeof html).toBe('string')
  })

  it('includes shop name', () => {
    const html = buildReceiptHtml({ order: baseOrder, config: baseConfig })
    expect(html).toContain('Test Shop')
  })

  it('includes order reference', () => {
    const html = buildReceiptHtml({ order: baseOrder, config: baseConfig })
    expect(html).toContain('OT-20240101-0001')
  })

  it('includes all product names', () => {
    const html = buildReceiptHtml({ order: baseOrder, config: baseConfig })
    expect(html).toContain('Widget')
    expect(html).toContain('Gadget')
  })

  it('includes total amount', () => {
    const html = buildReceiptHtml({ order: baseOrder, config: baseConfig })
    expect(html).toContain('19.99')
  })

  it('includes VAT breakdown when enabled', () => {
    const html = buildReceiptHtml({ order: baseOrder, config: baseConfig })
    expect(html).toContain('IVA 21%')
    expect(html).toContain('IVA 10%')
  })

  it('omits VAT breakdown when disabled', () => {
    const config = { ...baseConfig, receipt: { ...baseConfig.receipt, show_vat_breakdown: false } }
    const html = buildReceiptHtml({ order: baseOrder, config })
    expect(html).not.toContain('IVA 21%')
  })

  it('includes cash change when payment is CASH', () => {
    const html = buildReceiptHtml({
      order: baseOrder,
      config: baseConfig,
      paymentMethod: 'CASH',
      amountReceived: 30.00,
    })
    expect(html).toContain('Change')
    expect(html).toContain('10.01')
  })

  it('includes discount row when discount applied', () => {
    const html = buildReceiptHtml({
      order: { ...baseOrder, total: 14.99 },
      config: baseConfig,
      discountAmount: 5.00,
    })
    expect(html).toContain('Discount')
    expect(html).toContain('-5.00')
  })

  it('includes shop address', () => {
    const html = buildReceiptHtml({ order: baseOrder, config: baseConfig })
    expect(html).toContain('123 Main St')
  })

  it('includes tax ID', () => {
    const html = buildReceiptHtml({ order: baseOrder, config: baseConfig })
    expect(html).toContain('B12345678')
  })

  it('includes receipt footer', () => {
    const html = buildReceiptHtml({ order: baseOrder, config: baseConfig })
    expect(html).toContain('Thank you!')
  })

  it('uses 80mm paper width', () => {
    const html = buildReceiptHtml({ order: baseOrder, config: baseConfig })
    expect(html).toContain('80mm')
  })

  it('handles order with no customer info gracefully', () => {
    const orderNoCustomer = { ...baseOrder, customer_name: '', customer_email: '' }
    const html = buildReceiptHtml({ order: orderNoCustomer, config: baseConfig })
    expect(html).toContain('OT-20240101-0001')
  })

  it('handles missing config gracefully', () => {
    const html = buildReceiptHtml({ order: baseOrder, config: {} })
    expect(typeof html).toBe('string')
  })
})
