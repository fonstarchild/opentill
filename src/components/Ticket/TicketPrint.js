/**
 * Opentill — Thermal receipt printer
 *
 * Generates an 80mm receipt HTML and either:
 *  - Opens a print window (browser/Tauri)
 *  - Returns the HTML string for preview
 *
 * Fully configurable via the shop config object.
 * VAT breakdown is legally required on simplified invoices (Spain, EU)
 * per Art. 6 RD 1619/2012 (Reglamento de facturación).
 *
 * @param {object} params
 * @param {object} params.order        - Order object from the backend
 * @param {object} params.config       - Shop config (shop, currency, locale, receipt)
 * @param {string} [params.paymentMethod]
 * @param {number} [params.amountReceived]
 * @param {number} [params.discountAmount]
 * @param {object} [params.labels]     - Translated strings (pass t() results here)
 */

// ── VAT breakdown calculator ─────────────────────────────────────────────────
// Each item must carry its own tax_rate (decimal: 0.21, 0.10, 0.04, 0.00).
// We compute base imponible and cuota (tax amount) per rate and apply any
// proportional discount before splitting into base/cuota.
function buildVatBreakdown(items, discountAmount) {
  const byRate = {}
  let grandTotal = 0

  for (const item of items) {
    const rate = parseFloat(item.tax_rate ?? 0.21)
    const qty  = item.quantity ?? 1
    const price = parseFloat(item.unit_price ?? item.price ?? 0)
    const lineTotal = price * qty
    grandTotal += lineTotal
    const key = rate.toFixed(4)
    if (!byRate[key]) byRate[key] = { rate, totalInclusive: 0 }
    byRate[key].totalInclusive += lineTotal
  }

  const discount = parseFloat(discountAmount ?? 0)

  return Object.values(byRate)
    .sort((a, b) => b.rate - a.rate)
    .map(({ rate, totalInclusive }) => {
      // Apply discount proportionally to each rate bucket
      const share    = grandTotal > 0 ? totalInclusive / grandTotal : 1
      const adjusted = totalInclusive - discount * share
      const base     = rate === 0 ? adjusted : adjusted / (1 + rate)
      const cuota    = adjusted - base
      const pct      = Math.round(rate * 100)
      return {
        rate,
        pct,
        label: `${pct}%`,
        base:  Math.round(base  * 100) / 100,
        cuota: Math.round(cuota * 100) / 100,
        total: Math.round(adjusted * 100) / 100,
      }
    })
}

// ── Default labels (English fallback) ───────────────────────────────────────
const DEFAULT_LABELS = {
  subtotal:    'Subtotal',
  discount:    'Discount',
  total:       'TOTAL',
  payment:     'Payment',
  received:    'Received',
  change:      'Change',
  vatTitle:    'VAT breakdown',
  vatBase:     'Base',
  vatQuota:    'Tax',
  vatTotal:    'Total',
}

// ── Main builder ─────────────────────────────────────────────────────────────
export function buildReceiptHtml({
  order,
  config,
  paymentMethod,
  amountReceived,
  discountAmount,
  labels = {},
}) {
  const shop     = config?.shop    ?? {}
  const receipt  = config?.receipt ?? {}
  const currency = config?.currency ?? 'EUR'
  const locale   = config?.locale   ?? 'es-ES'
  const lbl      = { ...DEFAULT_LABELS, ...labels }

  const widthMm  = receipt.paper_width_mm ?? 80
  const showVat  = receipt.show_vat_breakdown !== false

  const now     = new Date()
  const dateStr = now.toLocaleDateString(locale)
  const timeStr = now.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' })

  const total    = parseFloat(order.total ?? 0)
  const discount = parseFloat(discountAmount ?? 0)
  const subtotal = total + discount
  const received = parseFloat(amountReceived ?? 0)
  const change   = paymentMethod === 'CASH' && received > 0 ? Math.max(received - total, 0) : null

  const lineItems = order.items ?? []

  // ── Line items ─────────────────────────────────────────────────────────────
  const itemRows = lineItems.map((item) => {
    const name  = item.product_name ?? item.name ?? '—'
    const qty   = item.quantity ?? 1
    const price = parseFloat(item.unit_price ?? item.price ?? 0)
    const rate  = parseFloat(item.tax_rate ?? 0.21)
    const pct   = Math.round(rate * 100)
    return `
      <tr>
        <td colspan="2" class="item-name">${name}</td>
      </tr>
      <tr>
        <td class="item-qty">${qty} &times; ${price.toFixed(2)} ${currency} <span class="tax-tag">${pct}% IVA</span></td>
        <td class="item-total">${(price * qty).toFixed(2)} ${currency}</td>
      </tr>`
  }).join('')

  // ── VAT breakdown ──────────────────────────────────────────────────────────
  const vatRows = showVat ? buildVatBreakdown(lineItems, discount) : []
  const vatTableRows = vatRows.map(({ label, base, cuota, total: t }) => `
    <tr>
      <td>IVA ${label}</td>
      <td class="right">${base.toFixed(2)}</td>
      <td class="right">${cuota.toFixed(2)}</td>
      <td class="right">${t.toFixed(2)}</td>
    </tr>`).join('')

  // ── HTML ───────────────────────────────────────────────────────────────────
  return `<!DOCTYPE html>
<html lang="${locale.slice(0, 2)}">
<head>
  <meta charset="UTF-8" />
  <title>Ticket ${order.reference}</title>
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    @page { size: ${widthMm}mm auto; margin: 4mm 0; }
    body {
      font-family: 'Courier New', monospace;
      font-size: 12px;
      width: ${widthMm}mm;
      color: #000;
      background: #fff;
      padding: 0 4mm;
    }
    .center { text-align: center; }
    .right  { text-align: right; }
    .bold   { font-weight: bold; }
    .big    { font-size: 15px; font-weight: 700; letter-spacing: 0.04em; }
    .small  { font-size: 10px; }
    .sep    { border: none; border-top: 1px dashed #000; margin: 4px 0; }
    table   { width: 100%; border-collapse: collapse; }

    .item-name  { padding-top: 3px; font-size: 11px; word-break: break-word; }
    .item-qty   { padding-bottom: 3px; color: #444; font-size: 11px; }
    .item-total { padding-bottom: 3px; text-align: right; font-weight: bold; }
    .tax-tag    { font-size: 8px; color: #777; }

    .summary-row td    { padding: 1px 0; }
    .summary-value     { text-align: right; font-weight: bold; }
    .total-row td      { padding-top: 4px; font-size: 14px; font-weight: 700; border-top: 1px solid #000; }

    /* VAT table — legally required on Spanish simplified invoices */
    .vat-section       { margin-top: 2px; }
    .vat-title         { font-size: 9px; font-weight: bold; margin-bottom: 1px; }
    .vat-table         { font-size: 9px; }
    .vat-table th,
    .vat-table td      { padding: 1px 0; text-align: right; }
    .vat-table th:first-child,
    .vat-table td:first-child { text-align: left; }
    .vat-table thead tr { border-bottom: 1px solid #aaa; }
    .vat-table .vat-total-row td { border-top: 1px solid #aaa; font-weight: bold; }

    .footer { font-size: 9px; color: #555; text-align: center; margin-top: 6px; }

    @media print { body { width: ${widthMm}mm; } }
  </style>
</head>
<body>

  <!-- Shop header -->
  <p class="center bold big">${shop.name ?? 'Opentill'}</p>
  ${shop.address ? `<p class="center small">${shop.address}</p>` : ''}
  ${shop.phone   ? `<p class="center small">Tel: ${shop.phone}</p>` : ''}
  ${shop.tax_id  ? `<p class="center small">NIF/CIF: ${shop.tax_id}</p>` : ''}

  <hr class="sep" />

  <!-- Date / reference -->
  <p class="center small">${dateStr}&nbsp;&nbsp;${timeStr}</p>
  <p class="center bold">Ref: ${order.reference}</p>
  ${order.customer_name  ? `<p class="center small">${order.customer_name}</p>` : ''}
  ${order.customer_email ? `<p class="center small">${order.customer_email}</p>` : ''}

  <hr class="sep" />

  <!-- Line items -->
  <table><tbody>${itemRows}</tbody></table>

  <hr class="sep" />

  <!-- Totals -->
  <table class="summary-row"><tbody>
    ${discount > 0 ? `
    <tr><td>${lbl.subtotal}</td><td class="summary-value">${subtotal.toFixed(2)} ${currency}</td></tr>
    <tr><td>${lbl.discount}</td><td class="summary-value">-${discount.toFixed(2)} ${currency}</td></tr>
    ` : ''}
    <tr class="total-row">
      <td>${lbl.total}</td>
      <td class="right">${total.toFixed(2)} ${currency}</td>
    </tr>
    <tr><td>${lbl.payment}</td><td class="summary-value">${paymentMethod ?? ''}</td></tr>
    ${change !== null && received > 0 ? `
    <tr><td>${lbl.received}</td><td class="summary-value">${received.toFixed(2)} ${currency}</td></tr>
    <tr><td>${lbl.change}</td><td class="summary-value">${change.toFixed(2)} ${currency}</td></tr>
    ` : ''}
  </tbody></table>

  ${vatRows.length > 0 ? `
  <hr class="sep" />
  <!-- VAT breakdown (Art. 6 RD 1619/2012 — Reglamento de facturación) -->
  <div class="vat-section">
    <p class="vat-title">${lbl.vatTitle}</p>
    <table class="vat-table">
      <thead>
        <tr>
          <th>Tipo</th>
          <th>${lbl.vatBase}</th>
          <th>Cuota</th>
          <th>${lbl.vatTotal}</th>
        </tr>
      </thead>
      <tbody>
        ${vatTableRows}
        <tr class="vat-total-row">
          <td>TOTAL</td>
          <td class="right">${vatRows.reduce((s, r) => s + r.base, 0).toFixed(2)}</td>
          <td class="right">${vatRows.reduce((s, r) => s + r.cuota, 0).toFixed(2)}</td>
          <td class="right">${total.toFixed(2)}</td>
        </tr>
      </tbody>
    </table>
  </div>` : ''}

  <hr class="sep" />
  ${shop.receipt_footer ? `<p class="footer">${shop.receipt_footer}</p>` : ''}
  ${shop.website        ? `<p class="footer">${shop.website}</p>` : ''}
  <p class="footer small" style="margin-top:4px">FACTURA SIMPLIFICADA</p>
  <br/>
</body>
</html>`
}

// ── Print helper ─────────────────────────────────────────────────────────────
export function printReceipt(params) {
  const html = buildReceiptHtml(params)
  const win  = window.open('', '_blank', 'width=400,height=700,toolbar=0,menubar=0,scrollbars=1')
  if (!win) {
    alert('Popup blocked. Please allow popups for this app.')
    return
  }
  win.document.write(html)
  win.document.close()
  win.onload = () => {
    win.focus()
    win.print()
    win.onafterprint = () => win.close()
  }
}
