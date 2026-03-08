# Opentill

> **Open-source point of sale for physical shops — works anywhere, needs nothing but a receipt printer and a barcode scanner.**

Opentill is a free, self-hosted POS application designed to run on any computer without internet, without subscriptions, and without vendor lock-in. It installs like any desktop app and stores all data locally on the device.

Built with [Tauri v2](https://v2.tauri.app/) + React + FastAPI · Runs on **Windows, macOS and Linux**

---

## Why Opentill?

Most POS solutions are cloud-only, expensive, or require proprietary hardware. Opentill is different:

- **No subscription** — install it, own it, use it forever
- **No internet required** — fully offline after install
- **No proprietary hardware** — any thermal printer + any USB/Bluetooth barcode scanner works
- **Open source** — MIT license, fork it, extend it, contribute back
- **Multilingual** — English, Spanish, French, German, Italian, Portuguese, Dutch, Polish

The goal is a POS that any small shop owner can install in five minutes with hardware they already have or can buy for under €100.

---

## Minimum hardware

| Component | Requirement |
|---|---|
| Computer | Any Windows 10+, macOS 12+, or Linux (Ubuntu 20.04+) machine |
| Receipt printer | Any **80mm thermal printer** with USB or Bluetooth (ESC/POS compatible) |
| Barcode scanner | Any **USB or Bluetooth HID barcode scanner** — plug and play, no drivers needed |
| RAM | 512 MB minimum |
| Disk | ~150 MB |

> **That's it.** No touchscreen required, no dedicated POS terminal, no cloud account.

---

## Features

| | |
|---|---|
| **Point of Sale** | Search or scan products, manage cart, apply discounts, charge sales |
| **Barcode scanning** | Plug in any HID scanner — it works instantly as keyboard input |
| **Receipt printing** | 80mm thermal paper with full VAT breakdown, shop logo and custom footer |
| **Catalog** | Products with stock, SKU, barcode, categories, VAT rates |
| **Order history** | Full history with void/refund and stock restoration |
| **Metrics** | Revenue, order count, average ticket, daily/monthly charts, top products |
| **Payment methods** | Cash, manual card terminal, Bizum, Stripe Terminal, SumUp — extensible |
| **Configuration** | Shop info, currency, locale, receipt settings, payment providers |
| **Offline-first** | SQLite database stored locally — no internet needed |

---

## Quick start (development)

### Prerequisites

- [Node.js](https://nodejs.org/) 20+
- [Rust](https://rustup.rs/) stable
- [Python](https://python.org/) 3.12+
- [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/) for your OS

### 1. Install dependencies

```bash
npm install
pip install -r backend/requirements.txt
```

### 2. Start the backend

```bash
npm run backend:dev
# FastAPI on http://localhost:47821
# API docs at http://localhost:47821/docs
```

### 3. Start the desktop app

```bash
npm run tauri:dev
```

---

## Build for production

The build is **two independent steps** that must run in order:

```bash
# Step 1 — PyInstaller bundles the Python backend into a self-contained binary
#           Output: src-tauri/binaries/opentill-backend-<platform>
node scripts/build-backend.js

# Step 2 — Tauri compiles the frontend + Rust shell, then copies the binary
#           produced in step 1 into the final installer. It does NOT recompile
#           the backend — it just packages whatever is in src-tauri/binaries/.
npm run tauri:build
```

If you skip step 1 (or the binary is stale), `tauri:build` will fail or ship an outdated backend.

Installer output: `src-tauri/target/release/bundle/`

To build for all three platforms automatically, push a version tag — see [Releases](#releases) below.

---

## Adding a payment provider

1. Create `backend/payments/infrastructure/providers/my_provider.py`:

```python
from ...domain.payment_provider import IPaymentProvider, PaymentResult, ConfigField

class MyProvider(IPaymentProvider):
    id = "MY_PROVIDER"
    name = "My Provider"
    is_online = True

    @classmethod
    def get_config_schema(cls):
        return [
            ConfigField(key="api_key", label="API Key", type="password", required=True),
        ]

    def charge(self, amount, currency, metadata):
        # your integration here
        return PaymentResult(success=True, transaction_id="...")
```

2. Register it in `backend/payments/infrastructure/registry.py`:

```python
from .providers.my_provider import MyProvider
PROVIDERS[MyProvider.id] = MyProvider
```

It appears automatically in Settings.

---

## Releases

Push a version tag to trigger GitHub Actions builds for all three platforms:

```bash
git tag v1.0.0
git push origin v1.0.0
```

This creates a GitHub Release draft with installers for Windows (`.msi`), macOS (`.dmg`) and Linux (`.deb` / `.AppImage`).

---

## Project structure

```
backend/          Python FastAPI backend (runs as embedded sidecar)
  catalog/        Products bounded context
  sales/          Orders bounded context
  payments/       Payment providers
  configuration/  Shop config
  shared/         DDD base classes
src/              React frontend
  pages/          POSPage, CatalogPage, OrdersPage, MetricsPage, SettingsPage
  components/     Shared UI components
  store/          Zustand state (cart, config)
  api/            HTTP client wrappers
  i18n/           Translations (8 languages)
src-tauri/        Tauri shell (Rust)
scripts/          Build helpers
```

---

## Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

Areas where contributions are especially welcome:
- Additional payment providers (PayPal, Redsys, Square, …)
- ESC/POS direct printing support
- E-commerce sync connectors (WooCommerce, Shopify, PrestaShop)
- Additional languages

---

## License

MIT — free to use, modify and distribute.
