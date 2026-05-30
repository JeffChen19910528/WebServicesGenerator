# Web Services Generator

[繁體中文](#繁體中文) | [English](#english)

---

## 繁體中文

一個能自動建立 Web Services 專案的製造器工具。只需在介面填寫欄位，即可產生多種語言/框架的完整專案代碼並下載，同時支援輸出 SOAP XML、SoapUI Project、Postman Collection 等測試格式。

現支援從 **MS SQL Server 資料庫** 直接匯入結構，自動產生 CRUD 服務定義，無需手動填寫方法與資料模型。

介面支援 **English / 繁體中文** 語系切換，點擊右上角的 EN | 繁中 按鈕即可切換。

---

### 功能

- **支援 SOAP 與 REST**：可選擇只產生 SOAP、只產生 REST，或同時產生兩者
- **21 種語言/框架輸出**：涵蓋 Java、Python、Node.js、C#、PHP、Go、Ruby
- **3 種測試格式**：SOAP XML Envelope、SoapUI Project、Postman Collection
- **ZIP 下載**：所有產生的檔案打包成 ZIP 直接下載
- **5 步驟精靈介面**：引導式表單，逐步填寫服務定義
- **MS SQL Server 匯入**：連線資料庫、選擇資料表、設定 CRUD 操作，自動產生完整服務定義
- **多語系 UI**：English / 繁體中文 即時切換

---

### 支援的框架

#### SOAP
| 框架 | 語言 |
|------|------|
| Spring-WS | Java |
| Apache CXF | Java |
| spyne | Python |
| soap (npm) | Node.js |
| CoreWCF | C# |
| SoapServer | PHP |
| net/http + WSDL | Go |

#### REST
| 框架 | 語言 |
|------|------|
| Spring Boot | Java |
| FastAPI | Python |
| Flask | Python |
| Django REST Framework | Python |
| Express | Node.js |
| NestJS | Node.js |
| Fastify | Node.js |
| ASP.NET Core Web API | C# |
| Laravel | PHP |
| Slim 4 | PHP |
| Gin | Go |
| Echo | Go |
| Rails API | Ruby |
| Sinatra | Ruby |

---

### 快速開始

#### 需求環境

- Python 3.10+
- Node.js 18+
- npm
- （選用）MS SQL Server ODBC 驅動程式（使用資料庫匯入功能時需要）

#### 一鍵啟動（Windows）

直接雙擊 **`start.bat`** 即可。腳本會自動：
1. 檢查 Python 與 Node.js 是否安裝
2. 安裝後端與前端所需套件（首次執行需等待）
3. 開啟後端（port 8000）與前端（port 5173）服務
4. 自動在瀏覽器開啟 `http://localhost:5173`

**停止服務**：雙擊 **`stop.bat`**，會自動關閉所有相關行程。

> 若 Windows 顯示安全性警告，請點選「更多資訊」→「仍要執行」。

#### 手動啟動

**後端：**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

後端啟動後可在 `http://localhost:8000/docs` 查看 API 文件（Swagger UI）。

**前端（另開終端機）：**
```bash
cd frontend
npm install
npm run dev
```

開啟瀏覽器前往 `http://localhost:5173`

---

### 使用說明

#### Step 1 — 基本資訊

| 欄位 | 說明 | 範例 |
|------|------|------|
| Service Name | 服務名稱 | `UserService` |
| Service Type | 服務類型 | SOAP / REST / BOTH |
| Namespace | XML 命名空間（SOAP 必填） | `http://example.com/service` |
| Description | 服務描述 | 選填 |
| Version | 版本號 | `1.0` |

#### Step 2 — 方法

新增服務的操作方法，每個方法可設定名稱、回傳型別、HTTP Method、路徑與參數列表。

#### Step 3 — 資料模型

定義複雜型別，每個 Model 可包含多個 Field（名稱、型別、是否必填）。

#### Step 4 — 選擇框架

勾選想要產生的輸出框架，根據服務類型自動篩選。

#### Step 5 — 下載

- **下載專案代碼**：每個框架各有一個下載按鈕，下載對應語言的完整專案 ZIP
- **下載測試檔案**：選擇 SOAP XML、SoapUI Project 或 Postman Collection 格式後下載

---

### MS SQL Server 資料庫匯入

點擊首頁的「**從資料庫匯入**」按鈕進入 5 步驟精靈：

| 步驟 | 說明 |
|------|------|
| Step 1 — 連線設定 | 填寫伺服器位址、資料庫名稱、驗證方式（SQL / Windows 整合驗證） |
| Step 2 — 選擇資料表 | 瀏覽資料庫中所有資料表，勾選要匯入的項目 |
| Step 3 — 操作設定 | 為每個資料表選擇要產生的操作（getAll、getById、create、update、delete），並設定服務名稱與類型 |
| Step 4 — 選擇框架 | 選擇輸出的語言/框架 |
| Step 5 — 下載 | 下載自動產生的專案 ZIP |

> 需要安裝 [ODBC Driver for SQL Server](https://learn.microsoft.com/zh-tw/sql/connect/odbc/download-odbc-driver-for-sql-server)（17 或 18 版）。

---

### 執行測試

#### 後端測試（pytest）

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

共 **449 個測試**，全部通過。

#### 前端測試（Vitest）

```bash
cd frontend
npm install
npm test
```

測試涵蓋範圍：
- **App.test.jsx** — 精靈導覽、步驟切換、API 呼叫（25 個測試）
- **BasicInfo.test.jsx** — 表單欄位渲染與狀態更新（13 個測試）
- **MethodBuilder.test.jsx** — 動態新增/刪除方法與參數（21 個測試）
- **ModelBuilder.test.jsx** — 動態新增/刪除模型與欄位（20 個測試）
- **FrameworkSelector.test.jsx** — 框架勾選、依服務類型篩選（17 個測試）
- **StepIndicator.test.jsx** — 步驟指示器狀態（17 個測試）
- **DownloadPanel.test.jsx** — 下載按鈕、loading 狀態、錯誤處理（31 個測試）
- **i18n.test.jsx** — 語系切換、翻譯完整性、LanguageContext（17 個測試）

共 **161 個測試**，全部通過。

後端新增資料庫功能測試：
- **test_db_api.py** — `/api/database/*` 端點整合測試（mock pyodbc，18 個測試）
- **test_db_to_service.py** — Schema 轉換邏輯單元測試（24 個測試）

---

## English

A web service project generator. Fill in the form fields and generate complete project code for multiple languages/frameworks, with support for SOAP XML, SoapUI Project, and Postman Collection test artifacts.

You can also **import directly from an MS SQL Server database** — connect, pick tables, choose CRUD operations, and the service definition is built automatically.

The UI supports **English / 繁體中文** language switching — click the EN | 繁中 button in the top-right corner of the header.

---

### Features

- **SOAP & REST support**: Generate SOAP only, REST only, or both
- **21 language/framework outputs**: Java, Python, Node.js, C#, PHP, Go, Ruby
- **3 test formats**: SOAP XML Envelope, SoapUI Project, Postman Collection
- **ZIP download**: All generated files bundled as a ZIP
- **5-step wizard UI**: Guided form for step-by-step service definition
- **MS SQL Server import**: Connect to a database, select tables, configure CRUD operations, and auto-generate a complete service definition
- **Multi-language UI**: Switch between English and Traditional Chinese instantly

---

### Supported Frameworks

#### SOAP
| Framework | Language |
|-----------|----------|
| Spring-WS | Java |
| Apache CXF | Java |
| spyne | Python |
| soap (npm) | Node.js |
| CoreWCF | C# |
| SoapServer | PHP |
| net/http + WSDL | Go |

#### REST
| Framework | Language |
|-----------|----------|
| Spring Boot | Java |
| FastAPI | Python |
| Flask | Python |
| Django REST Framework | Python |
| Express | Node.js |
| NestJS | Node.js |
| Fastify | Node.js |
| ASP.NET Core Web API | C# |
| Laravel | PHP |
| Slim 4 | PHP |
| Gin | Go |
| Echo | Go |
| Rails API | Ruby |
| Sinatra | Ruby |

---

### Quick Start

#### Requirements

- Python 3.10+
- Node.js 18+
- npm
- (Optional) MS SQL Server ODBC Driver 17 or 18 — required only for the database import feature

#### One-Click Start (Windows)

Double-click **`start.bat`**. The script will:
1. Check Python and Node.js installations
2. Install backend and frontend dependencies (first run takes a moment)
3. Start the backend (port 8000) and frontend (port 5173)
4. Open `http://localhost:5173` in your browser automatically

**Stop services**: Double-click **`stop.bat`**.

> If Windows shows a security warning, click "More info" → "Run anyway".

#### Manual Start

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API documentation (Swagger UI) is available at `http://localhost:8000/docs`.

**Frontend (open a separate terminal):**
```bash
cd frontend
npm install
npm run dev
```

Open your browser at `http://localhost:5173`.

---

### Usage

#### Step 1 — Basic Info

| Field | Description | Example |
|-------|-------------|---------|
| Service Name | Name of the service | `UserService` |
| Service Type | Protocol type | SOAP / REST / BOTH |
| Namespace | XML namespace (SOAP) | `http://example.com/service` |
| Description | Service description | optional |
| Version | Version string | `1.0` |

#### Step 2 — Methods

Add operations your service exposes. Each method has a name, return type, HTTP method, path, and a parameter list.

#### Step 3 — Data Models

Define reusable complex types. Each model contains fields with a name, type, and required flag.

#### Step 4 — Select Frameworks

Check the frameworks you want code generated for. The list is filtered automatically based on service type.

#### Step 5 — Download

- **Download project code**: One button per framework; each downloads a complete project ZIP
- **Download test files**: Select SOAP XML, SoapUI Project, or Postman Collection, then download

---

### MS SQL Server Database Import

Click **"Import from Database"** on the home screen to open the 5-step import wizard:

| Step | Description |
|------|-------------|
| Step 1 — Connection | Enter server address, database name, and authentication (SQL / Windows Integrated) |
| Step 2 — Select Tables | Browse all tables in the database and check the ones to import |
| Step 3 — Operations | Choose CRUD operations for each table (getAll, getById, create, update, delete), set service name and type |
| Step 4 — Frameworks | Select output language/framework |
| Step 5 — Download | Download the auto-generated project ZIP |

> Requires [ODBC Driver for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) (version 17 or 18).

---

### API Reference

#### `GET /api/frameworks`

Returns all supported frameworks.

**Response:**
```json
{
  "soap": [{"id": "soap-java-spring-ws", "label": "Java (Spring-WS)"}, ...],
  "rest": [{"id": "rest-python-fastapi", "label": "Python (FastAPI)"}, ...]
}
```

#### `POST /api/generate`

Generates project code for a given framework. Returns a ZIP file.

**Request body:**
```json
{
  "service": {
    "service_name": "UserService",
    "service_type": "REST",
    "namespace": "http://example.com/userservice",
    "version": "1.0",
    "methods": [...],
    "models": [...]
  },
  "framework": "rest-python-fastapi"
}
```

#### `POST /api/generate-tests`

Generates test artifact files. Returns a ZIP file.

**Request body:**
```json
{
  "service": { ... },
  "test_types": ["soap-xml", "soapui", "postman"]
}
```

---

### Running Tests

#### Backend tests (pytest)

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

**449 tests**, all passing.

#### Frontend tests (Vitest)

```bash
cd frontend
npm install
npm test
```

| Test file | Coverage | Count |
|-----------|----------|-------|
| App.test.jsx | Wizard navigation, step switching, API calls | 25 |
| BasicInfo.test.jsx | Form field rendering and state updates | 13 |
| MethodBuilder.test.jsx | Add/remove methods and parameters | 21 |
| ModelBuilder.test.jsx | Add/remove models and fields | 20 |
| FrameworkSelector.test.jsx | Checkbox selection, filtering by service type | 17 |
| StepIndicator.test.jsx | Step indicator state | 17 |
| DownloadPanel.test.jsx | Download buttons, loading state, error handling | 31 |
| i18n.test.jsx | Language switching, translation completeness, LanguageContext | 17 |

**161 tests**, all passing.

New backend database tests:

| Test file | Coverage | Count |
|-----------|----------|-------|
| test_db_api.py | `/api/database/*` endpoint integration tests (mocked pyodbc) | 18 |
| test_db_to_service.py | Schema-to-service conversion unit tests | 24 |

---

### Project Structure

```
webservices/
├── backend/
│   ├── main.py                      # FastAPI main app
│   ├── models.py                    # Pydantic data models
│   ├── db_connector.py              # MS SQL Server connection & schema extraction
│   ├── db_to_service.py             # Convert DB schema to ServiceDefinition
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── generators/
│   │   ├── __init__.py              # get_generator() factory
│   │   ├── base.py                  # BaseGenerator abstract class
│   │   ├── soap/                    # 7 SOAP generators
│   │   └── rest/                    # 14 REST generators
│   ├── test_generators/
│   │   ├── soap_xml.py
│   │   ├── soapui_project.py
│   │   └── postman_collection.py
│   └── tests/
│       ├── conftest.py
│       ├── test_models.py
│       ├── test_api.py
│       ├── test_generators_soap.py
│       ├── test_generators_rest.py
│       ├── test_test_generators.py
│       ├── test_db_api.py           # /api/database/* endpoint tests
│       └── test_db_to_service.py    # Schema conversion unit tests
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── vitest.config.js
    ├── index.html
    └── src/
        ├── App.jsx                  # 5-step wizard controller
        ├── App.css
        ├── main.jsx
        ├── i18n/
        │   ├── translations.js      # EN / zh-TW translation strings
        │   └── LanguageContext.jsx  # React context + useLanguage hook
        ├── components/
        │   ├── BasicInfo.jsx
        │   ├── MethodBuilder.jsx
        │   ├── ModelBuilder.jsx
        │   ├── FrameworkSelector.jsx
        │   ├── DownloadPanel.jsx
        │   ├── StepIndicator.jsx
        │   └── DatabaseWizard.jsx   # MS SQL Server import wizard
        └── tests/
            ├── testUtils.jsx        # renderWithLang helper
            ├── i18n.test.jsx
            ├── App.test.jsx
            ├── BasicInfo.test.jsx
            ├── MethodBuilder.test.jsx
            ├── ModelBuilder.test.jsx
            ├── FrameworkSelector.test.jsx
            ├── StepIndicator.test.jsx
            └── DownloadPanel.test.jsx
```

---

#### `POST /api/database/connect`

Connects to MS SQL Server and returns the list of tables.

**Request body:**
```json
{
  "server": "localhost",
  "port": 1433,
  "database": "MyDB",
  "username": "sa",
  "password": "secret",
  "auth_type": "sql"
}
```

**Response:**
```json
{
  "tables": [
    {"schema": "dbo", "table_name": "Product", "full_name": "dbo.Product"}
  ]
}
```

#### `POST /api/database/schema`

Returns column metadata for the selected tables. Accepts the same connection fields plus a `tables` list.

**Response:**
```json
{
  "schema": {
    "dbo.Product": [
      {"name": "Id", "sql_type": "int", "service_type": "integer",
       "is_nullable": false, "max_length": null, "is_primary_key": true}
    ]
  }
}
```

#### `POST /api/database/generate-service`

Generates a `ServiceDefinition` from the database schema. Accepts connection fields plus:
```json
{
  "tables": ["dbo.Product"],
  "operations": {"dbo.Product": ["getAll", "getById", "create", "update", "delete"]},
  "service_name": "ProductService",
  "service_type": "REST"
}
```

Returns a `ServiceDefinition` object (same schema as the `service` field in `/api/generate`).

---

### Adding a Custom Generator

1. Create a new Python file in `backend/generators/soap/` or `backend/generators/rest/`
2. Extend `BaseGenerator` and implement `generate() -> Dict[str, str]` (key = file path, value = file content)
3. Add the new framework ID to the `GENERATORS` dict in `backend/generators/__init__.py`
4. Add the corresponding label to the `/api/frameworks` response in `backend/main.py`
