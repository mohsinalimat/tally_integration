# Tally Integration - Project Structure

## 📁 Directory Structure

```
tally_erpnext/
├── README.md                          # Main README with overview
├── license.txt                        # GPL v3.0 license
├── pyproject.toml                     # Project dependencies
│
├── docs/                              # 📚 All documentation
│   ├── README.md                      # Documentation index
│   ├── QUICK_START_DOCTYPE.md         # Quick start guide (5 min)
│   ├── INSTALLATION.md                # Installation guide
│   ├── DOCTYPE_ARCHITECTURE.md        # Architecture guide
│   ├── PROJECT_STRUCTURE.md           # This file - project structure
│   ├── TALLY_INTEGRATION_GUIDE.md     # API reference
│   ├── SERVER_SCRIPTS_GUIDE.md        # Server Scripts examples
│   └── IMPLEMENTATION_SUMMARY.md      # Implementation overview
│
└── tally_erpnext/                 # 📦 Main app package
    ├── __init__.py
    ├── hooks.py                       # Frappe hooks
    ├── modules.txt                    # Module: Tally
    ├── patches.txt                    # Database patches
    │
    ├── public/                        # Static files (JS, CSS)
    │   └── .gitkeep
    │
    ├── templates/                     # Jinja templates
    │   ├── __init__.py
    │   └── pages/
    │       └── __init__.py
    │
    ├── config/                        # App configuration
    │   └── __init__.py
    │
    └── tally/                         # 🎯 Core module
        ├── __init__.py                # Module exports
        ├── client.py                  # TallyClient wrapper
        ├── api.py                     # Whitelisted API endpoints
        ├── utils.py                   # Utility functions
        ├── doctype_sync.py            # NEW: DocType sync engine
        │
        └── doctype/                   # ERPNext DocTypes
            ├── tally_settings/        # Configuration DocType
            │   ├── tally_settings.json
            │   ├── tally_settings.py
            │   ├── tally_settings.js
            │   └── __init__.py
            │
            ├── tally_sync_log/        # NEW: Audit trail
            │   ├── tally_sync_log.json
            │   ├── tally_sync_log.py
            │   └── __init__.py
            │
            ├── tally_ledger/          # NEW: Ledger DocType
            │   ├── tally_ledger.json
            │   ├── tally_ledger.py
            │   └── __init__.py
            │
            ├── tally_stock_item/      # NEW: Stock Item DocType
            │   ├── tally_stock_item.json
            │   ├── tally_stock_item.py
            │   └── __init__.py
            │
            ├── tally_voucher/         # NEW: Voucher DocType
            │   ├── tally_voucher.json
            │   ├── tally_voucher.py
            │   └── __init__.py
            │
            └── tally_voucher_ledger_entry/  # NEW: Child table
                ├── tally_voucher_ledger_entry.json
                ├── tally_voucher_ledger_entry.py
                └── __init__.py
```

## 📚 Documentation Files

All documentation is in the `/docs` directory:

| File | Purpose | Audience |
|------|---------|----------|
| [docs/README.md](docs/README.md) | Documentation index | All users |
| [docs/QUICK_START_DOCTYPE.md](docs/QUICK_START_DOCTYPE.md) | Get started in 5 minutes | New users |
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Installation guide | Admins |
| [docs/DOCTYPE_ARCHITECTURE.md](docs/DOCTYPE_ARCHITECTURE.md) | Architecture deep dive | Developers |
| [docs/TALLY_INTEGRATION_GUIDE.md](docs/TALLY_INTEGRATION_GUIDE.md) | API reference | Developers |
| [docs/SERVER_SCRIPTS_GUIDE.md](docs/SERVER_SCRIPTS_GUIDE.md) | Server Scripts | All users |
| [docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) | Complete overview | All users |

## 🔧 Core Python Files

### Integration Layer

**[tally_erpnext/tally/client.py](tally_erpnext/tally/client.py)**
- TallyClient wrapper class
- Connection management
- Error handling
- Frappe settings integration

**[tally_erpnext/tally/api.py](tally_erpnext/tally/api.py)**
- Whitelisted API endpoints
- Frontend callable methods
- CRUD operations

**[tally_erpnext/tally/utils.py](tally_erpnext/tally/utils.py)**
- Helper functions
- Data mapping utilities
- Legacy sync functions

### DocType Sync Engine (NEW!)

**[tally_erpnext/tally/doctype_sync.py](tally_erpnext/tally/doctype_sync.py)**
- `sync_ledgers_from_tally()` - Pull ledgers
- `sync_stock_items_from_tally()` - Pull items
- `sync_vouchers_from_tally()` - Pull vouchers
- `sync_ledger_to_tally()` - Push ledger
- `sync_stock_item_to_tally()` - Push item
- `sync_voucher_to_tally()` - Push voucher
- `create_sync_log()` - Create audit log

## 📋 DocType Definitions

### Configuration

**Tally Settings** (`tally_settings/`)
- Single DocType for app configuration
- Connection settings (host, port)
- Auto-sync options
- Test connection button

### Audit Trail (NEW!)

**Tally Sync Log** (`tally_sync_log/`)
- Logs all sync operations
- Tracks success/failure
- Stores Tally and ERP data
- Error messages and tracebacks

### Master Data (NEW!)

**Tally Ledger** (`tally_ledger/`)
- 1:1 mapping of Tally ledgers
- Links to Customer/Supplier/Account
- Auto-sync capability
- Balance tracking

**Tally Stock Item** (`tally_stock_item/`)
- 1:1 mapping of Tally stock items
- Links to Item
- Auto-sync capability
- Stock balance tracking

### Transactions (NEW!)

**Tally Voucher** (`tally_voucher/`)
- 1:1 mapping of Tally vouchers
- Links to Sales Invoice/Purchase Invoice/Payment Entry
- Submittable DocType
- Auto-sync on submit

**Tally Voucher Ledger Entry** (`tally_voucher_ledger_entry/`)
- Child table for voucher entries
- Ledger name, debit/credit, amount

## 🎯 Key Files Explained

### Entry Points

- `__init__.py` - Exports TallyClient and test_tally_connection
- `hooks.py` - Frappe hooks (scheduler events, doc events, etc.)

### Configuration

- `pyproject.toml` - Python dependencies (includes tally-integration)
- `modules.txt` - Defines "Tally" module

### Controllers

Each DocType has a `.py` controller file:
- Validation logic
- Auto-sync triggers
- Background job enqueueing
- Business logic

### JSON Definitions

Each DocType has a `.json` file defining:
- Fields and their properties
- Permissions
- Naming rules
- Child tables

### UI Scripts

- `tally_settings.js` - Test connection button handler
- Other DocTypes use default UI

## 📦 Dependencies

### Python (via pyproject.toml)

```toml
dependencies = [
    "tally-integration>=1.0.0",  # PyPI package for Tally XML API
]
```

### Frappe/ERPNext

- Minimum: v15.0
- Python: 3.10+

## 🔄 Data Flow

```
Tally Software (XML API)
    ↕
tally-integration (PyPI)
    ↕
TallyClient (client.py)
    ↕
DocType Sync Engine (doctype_sync.py)
    ↕
Tally DocTypes (ledger, item, voucher)
    ↕
Server Scripts (user-defined)
    ↕
ERPNext DocTypes (Customer, Item, Invoice)
```

## 📝 Usage Patterns

### 1. Direct API Usage

```python
from tally_erpnext.tally import TallyClient

client = TallyClient()
ledgers = client.get_ledgers()
```

### 2. DocType Sync

```python
from tally_erpnext.tally.doctype_sync import sync_ledgers_from_tally

result = sync_ledgers_from_tally()
```

### 3. Server Scripts

Add in ERPNext UI:
- DocType: Customer
- Event: After Insert
- Script: Create Tally Ledger

See [docs/SERVER_SCRIPTS_GUIDE.md](docs/SERVER_SCRIPTS_GUIDE.md)

### 4. API Endpoints

```javascript
frappe.call({
    method: "tally_erpnext.tally.doctype_sync.sync_all_ledgers",
    callback: function(r) { console.log(r.message); }
});
```

## 🎨 Customization Points

### 1. Add Custom Fields

Add custom fields to Tally DocTypes via Custom Field DocType

### 2. Modify Sync Logic

Edit `doctype_sync.py` to customize field mapping

### 3. Add Server Scripts

Create Server Scripts for custom automation

### 4. Extend DocTypes

Create custom DocTypes that link to Tally DocTypes

### 5. Add Scheduled Tasks

Add to `hooks.py`:
```python
scheduler_events = {
    "daily": ["tally_erpnext.tally.tasks.daily_sync"]
}
```

## 🚀 Deployment

### Development

```bash
bench get-app tally_erpnext
bench install-app tally_erpnext
cd apps/tally_erpnext
pip install -e .
bench migrate
bench restart
```

### Production

```bash
# Same as development, plus:
bench --site [site-name] migrate
sudo supervisorctl restart all
```

## 📊 Statistics

- **DocTypes**: 5 (Settings, Sync Log, Ledger, Stock Item, Voucher)
- **Python Files**: 8 core files
- **Documentation**: 7 comprehensive guides
- **Lines of Code**: ~2000+ (Python)
- **Server Script Examples**: 8 ready-to-use

## 🔍 Finding Things

### "Where is the sync logic?"
→ `tally_erpnext/tally/doctype_sync.py`

### "Where are the API endpoints?"
→ `tally_erpnext/tally/api.py`

### "How do I setup auto-sync?"
→ `docs/SERVER_SCRIPTS_GUIDE.md`

### "Where is the TallyClient?"
→ `tally_erpnext/tally/client.py`

### "Where are the DocType definitions?"
→ `tally_erpnext/tally/doctype/*/`

### "Where is the documentation?"
→ `docs/` directory

## 📖 Navigation

- [Main README](README.md)
- [Documentation Index](docs/README.md)
- [Quick Start](docs/QUICK_START_DOCTYPE.md)
- [Architecture](docs/DOCTYPE_ARCHITECTURE.md)

---

**Version**: 2.0 (DocType Architecture)
**Last Updated**: 2025-12-10
