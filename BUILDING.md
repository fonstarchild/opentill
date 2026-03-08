# Building Opentill

Opentill is a desktop app (Tauri) with a bundled Python backend (FastAPI via PyInstaller).
The result is a single installable file that works without Python, Node, or any other runtime.

---

## Prerequisites

### All platforms

| Tool | Version | Install |
|------|---------|---------|
| Node.js | ≥ 18 | https://nodejs.org |
| Python | 3.10 – 3.12 | https://python.org |
| Rust | stable | https://rustup.rs |

```bash
# Verify
node --version     # v18+
python3 --version  # 3.10 – 3.12
rustc --version    # 1.70+
```

### macOS (extra)

Xcode Command Line Tools are required for Rust to compile:

```bash
xcode-select --install
```

### Linux (extra)

WebKit and a few system libraries are required by Tauri:

```bash
# Ubuntu / Debian
sudo apt-get install -y \
  libwebkit2gtk-4.1-dev \
  libappindicator3-dev \
  librsvg2-dev \
  patchelf

# Fedora / RHEL
sudo dnf install -y \
  webkit2gtk4.1-devel \
  libappindicator-gtk3-devel \
  librsvg2-devel
```

### Windows (extra)

- Visual Studio Build Tools 2019+ with the **"Desktop development with C++"** workload
  (installed automatically by the Rust installer if you choose to do so)
- WebView2 is included in Windows 10 1803+ — no action needed

---

## First-time setup

```bash
# 1. Clone
git clone https://github.com/your-org/opentill.git
cd opentill

# 2. Python dependencies
pip install -r backend/requirements.txt pyinstaller

# 3. Node dependencies
npm install
```

---

## Building the executable

### Option A — two commands (recommended)

```bash
# Step 1: bundle the Python backend into a self-contained binary
npm run backend:build

# Step 2: compile the Tauri app and generate the installer
npm run tauri:build
```

After Step 2 the installers are in `src-tauri/target/release/bundle/`:

| Platform | Output |
|----------|--------|
| macOS | `macos/Opentill.app` and `dmg/Opentill_*.dmg` |
| Windows | `msi/Opentill_*_x64-setup.msi` |
| Linux | `deb/opentill_*.deb` and `appimage/opentill_*.AppImage` |

### Option B — .app only (faster, skips installer packaging)

```bash
npm run backend:build
npm run tauri:build -- --bundles app      # macOS
npm run tauri:build -- --bundles deb      # Linux
npm run tauri:build -- --bundles msi      # Windows
```

---

## Troubleshooting

### `PyInstaller not found`

```bash
pip install pyinstaller
# or, if pip resolves to a different Python:
python3 -m pip install pyinstaller
```

### `PYTHON` env var — use a specific Python binary

If you have multiple Python versions, point the build script to the right one:

```bash
PYTHON=python3.12 npm run backend:build
```

### Backend health check fails after build

The script verifies the binary by starting it and hitting `/api/health`.
Skip this if you know the build is fine (e.g. in CI without network access):

```bash
SKIP_VERIFY=1 npm run backend:build
```

### macOS — "app is damaged" / Gatekeeper warning

Without an Apple Developer certificate the binary is unsigned.
For **local testing** only:

```bash
# Ad-hoc sign (allows running on your own machine)
codesign --force --deep --sign - \
  src-tauri/binaries/opentill-backend-aarch64-apple-darwin

codesign --force --deep --sign - \
  "src-tauri/target/release/bundle/macos/Opentill.app"
```

Then right-click the `.app` → **Open** → **Open** to bypass Gatekeeper once.

### macOS — icons directory empty

If you see `failed to open icon ... No such file or directory`:

```bash
npm run tauri -- icon src-tauri/icons/app-icon.svg
```

This regenerates all icon sizes from the SVG source.

### Linux — `error: linker 'cc' not found`

```bash
sudo apt-get install build-essential
```

### Windows — long path errors during Rust compilation

Enable long paths in Windows:

```
Settings → System → For developers → Enable Win32 long paths
```

Or via registry:
```
HKLM\SYSTEM\CurrentControlSet\Control\FileSystem → LongPathsEnabled = 1
```

---

## Development mode (no installer needed)

To run the full app locally without building an installer:

```bash
# Terminal 1 — backend (auto-reload on code changes)
npm run backend:dev

# Terminal 2 — Tauri dev window (hot-reload frontend)
npm run tauri:dev
```

The dev window connects to the running backend automatically.

---

## GitHub Actions — automated releases

Pushing a tag triggers the release workflow which builds for all three platforms in parallel and creates a draft GitHub Release with the installers attached.

```bash
git tag v1.0.0
git push origin v1.0.0
```

The workflow file is at `.github/workflows/release.yml`.
Installers are uploaded as release assets automatically.
Publish the draft release manually from the GitHub UI when ready.

---

## What the build actually does

```
npm run backend:build
  └─ scripts/build-backend.js
       ├─ Detects platform + CPU arch (e.g. aarch64-apple-darwin)
       ├─ Runs: python3 -m PyInstaller --onefile backend/main_entry.py
       ├─ Moves binary → src-tauri/binaries/opentill-backend-<triple>[.exe]
       └─ Starts binary, polls /api/health to verify it works

npm run tauri:build
  └─ tauri build
       ├─ npm run build  (Vite → dist/)
       ├─ cargo build --release  (Rust Tauri shell)
       ├─ Copies backend binary into Opentill.app/Contents/MacOS/
       └─ Packages .app → .dmg / .msi / .deb / .AppImage
```

---

## Integrating with Opentill — Domain-Driven Design guide

Opentill's backend is structured around **Domain-Driven Design (DDD)**. This section explains how to understand, extend, or integrate with it from another system.

### The big picture

The backend is split into independent **bounded contexts**. Each one owns its data and exposes a clean HTTP interface. Nothing crosses context boundaries except through the API or explicit domain events.

```
backend/
  catalog/        → products, stock, barcodes
  sales/          → orders, order items, voids
  payments/       → payment providers and processing
  configuration/  → shop settings
  shared/         → base classes shared by all contexts
```

Each context follows the same internal structure:

```
<context>/
  domain/           Pure business logic — no framework, no DB
  application/      Use cases — orchestrate domain + infrastructure
  infrastructure/   SQLite persistence, external APIs
  interfaces/       FastAPI router — thin HTTP layer
```

---

### Layer by layer

#### Domain layer — the core

This is the heart of each context. It has **zero dependencies** on FastAPI, SQLModel, or any framework. It can run in a test with no database.

**Entities** have identity — two objects with the same `id` are the same thing regardless of their other fields:

```python
# backend/shared/domain/entity.py
class BaseEntity:
    def __init__(self, id):
        self.id = id

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id
```

**Aggregate roots** are entities that own a cluster of related objects and protect their invariants. External code can only modify them through their methods — never by reaching inside:

```python
# backend/sales/domain/order.py
class Order(AggregateRoot):
    def place(self, items, payment_method):
        if not items:
            raise EmptyOrderError("An order must have at least one item")
        self.items = items
        self.status = "COMPLETED"
        self.collect_event(OrderPlaced(order_id=self.id))

    def void(self):
        if self.status == "VOIDED":
            raise OrderAlreadyVoidedError(self.id)
        self.status = "VOIDED"
        self.collect_event(OrderVoided(order_id=self.id))
```

**Value objects** have no identity — they are equal when all their fields are equal, and they are immutable:

```python
# backend/shared/domain/value_object.py
class Money(ValueObject):
    def __init__(self, amount: Decimal, currency: str):
        if amount < 0:
            raise ValueError("Money amount cannot be negative")
        self.amount = amount
        self.currency = currency
```

**Domain events** record that something meaningful happened. They are collected on the aggregate and can be dispatched to other systems:

```python
class OrderPlaced(DomainEvent):
    event_type = "order.placed"
    # occurred_at, aggregate_id set automatically by AggregateRoot
```

---

#### Application layer — use cases

Use cases are plain Python classes with a single `execute()` method. They receive a command (input DTO), call domain objects, and return a result (output DTO). They have no knowledge of HTTP.

```python
# backend/sales/application/use_cases.py
class PlaceOrder:
    def __init__(self, order_repo: IOrderRepository, product_repo: IProductRepository):
        self.order_repo = order_repo
        self.product_repo = product_repo

    def execute(self, cmd: PlaceOrderCommand) -> OrderDTO:
        # 1. Load domain objects
        products = [self.product_repo.get(item.product_id) for item in cmd.items]

        # 2. Call domain logic (business rules enforced here)
        order = Order.create(products, cmd.payment_method, cmd.discount_amount)

        # 3. Persist
        self.order_repo.save(order)

        # 4. Return DTO (never expose domain objects to the HTTP layer)
        return OrderDTO.from_domain(order)
```

---

#### Infrastructure layer — persistence

Repositories implement the domain interfaces using SQLModel + SQLite. The domain never knows about tables or SQL.

```python
# backend/sales/infrastructure/repository.py
class SqlModelOrderRepository(IOrderRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, order: Order):
        row = OrderTable.from_domain(order)
        self.session.add(row)
        self.session.commit()

    def get(self, order_id: int) -> Order:
        row = self.session.get(OrderTable, order_id)
        if not row:
            raise NotFoundError(f"Order {order_id} not found")
        return row.to_domain()
```

---

#### Interfaces layer — HTTP

The FastAPI router is intentionally thin. It only handles HTTP concerns: parsing the request, calling the use case, returning the response. No business logic here.

```python
# backend/sales/interfaces/router.py
@router.post("/", response_model=OrderDTO, status_code=201)
def create_order(data: OrderCreateRequest, session: Session = Depends(get_session)):
    try:
        cmd = PlaceOrderCommand(items=..., payment_method=data.payment_method)
        return PlaceOrder(SqlModelOrderRepository(session), ...).execute(cmd)
    except DomainException as e:
        raise HTTPException(status_code=e.http_status, detail=str(e))
```

---

### How to add a new bounded context

Say you want to add a **Customers** context to track who buys what:

**1. Create the domain:**

```python
# backend/customers/domain/customer.py
class Customer(AggregateRoot):
    def __init__(self, id, name, email):
        super().__init__(id)
        self.name = name
        self.email = Email(email)   # value object validates format

    def rename(self, new_name: str):
        if not new_name.strip():
            raise ValidationError("Name cannot be blank")
        self.name = new_name
        self.collect_event(CustomerRenamed(aggregate_id=self.id, new_name=new_name))
```

**2. Define the repository interface in the domain:**

```python
# backend/customers/domain/repository.py
class ICustomerRepository(ABC):
    @abstractmethod
    def get(self, customer_id: int) -> Customer: ...
    @abstractmethod
    def save(self, customer: Customer): ...
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Customer]: ...
```

**3. Write use cases:**

```python
# backend/customers/application/use_cases.py
class CreateCustomer:
    def __init__(self, repo: ICustomerRepository):
        self.repo = repo

    def execute(self, cmd: CreateCustomerCommand) -> CustomerDTO:
        existing = self.repo.find_by_email(cmd.email)
        if existing:
            raise DuplicateEmailError(cmd.email)
        customer = Customer(id=None, name=cmd.name, email=cmd.email)
        self.repo.save(customer)
        return CustomerDTO.from_domain(customer)
```

**4. Implement persistence:**

```python
# backend/customers/infrastructure/sqlmodel_models.py
class CustomerTable(SQLModel, table=True):
    __tablename__ = "customer"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)
```

**5. Add the router and wire it in `main.py`:**

```python
# backend/customers/interfaces/router.py
router = APIRouter()

@router.post("/", response_model=CustomerDTO, status_code=201)
def create_customer(data: CreateCustomerRequest, session: Session = Depends(get_session)):
    ...

# backend/main.py
from backend.customers.interfaces.router import router as customers_router
app.include_router(customers_router, prefix="/api/customers")
```

---

### How to integrate an external system

Opentill exposes a standard REST API. Any external system can integrate by calling it directly.

**Read the full API docs** while the app is running:
```
http://localhost:47821/docs      ← Swagger UI
http://localhost:47821/redoc     ← ReDoc
```

**Key endpoints:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/catalog/` | List all products |
| `POST` | `/api/catalog/` | Create a product |
| `PATCH` | `/api/catalog/{id}` | Update a product |
| `POST` | `/api/catalog/{id}/adjust-stock` | Adjust stock |
| `GET` | `/api/orders/` | List orders |
| `POST` | `/api/orders/` | Place an order |
| `POST` | `/api/orders/{id}/void` | Void an order |
| `GET` | `/api/orders/metrics` | Sales metrics |
| `GET` | `/api/config/` | Get shop config |
| `PUT` | `/api/config/` | Update shop config |
| `GET` | `/api/payments/providers` | List payment providers |

**Example — create a product from an external system:**

```bash
curl -X POST http://localhost:47821/api/catalog/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Widget A",
    "sku": "WGT-001",
    "barcode": "8412345678901",
    "price": 9.99,
    "tax_rate": 0.21,
    "stock": 100,
    "category": "Widgets"
  }'
```

**Example — sync stock after a WooCommerce sale:**

```python
import httpx

def sync_stock(product_sku: str, quantity_sold: int):
    # Find product by SKU
    products = httpx.get("http://localhost:47821/api/catalog/", params={"q": product_sku}).json()
    product = next(p for p in products if p["sku"] == product_sku)

    # Deduct stock
    httpx.post(
        f"http://localhost:47821/api/catalog/{product['id']}/adjust-stock",
        json={"delta": -quantity_sold, "reason": "WooCommerce sale"}
    )
```

---

### Rules to follow when extending Opentill

1. **Domain logic lives only in the domain layer.** Never put business rules in routers or repositories.
2. **Contexts do not import from each other's domain.** If Sales needs product data, it gets it through `IProductRepository`, not by importing `Product` from the catalog domain.
3. **Repositories return domain objects, not table rows.** The infrastructure layer translates between the two.
4. **Use cases return DTOs, not domain objects.** Routers never touch aggregate internals.
5. **Every invariant is enforced in the domain.** If an order cannot be voided twice, that check lives in `Order.void()`, not in the router.
6. **Table names are explicit.** Always set `__tablename__` on SQLModel table classes to avoid naming conflicts.
