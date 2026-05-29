# Web Services Generator

一個能自動建立 Web Services 專案的製造器工具。只需在介面填寫欄位，即可產生多種語言/框架的完整專案代碼並下載，同時支援輸出 SOAP XML、SoapUI Project、Postman Collection 等測試格式。

---

## 功能

- **支援 SOAP 與 REST**：可選擇只產生 SOAP、只產生 REST，或同時產生兩者
- **21 種語言/框架輸出**：涵蓋 Java、Python、Node.js、C#、PHP、Go、Ruby
- **3 種測試格式**：SOAP XML Envelope、SoapUI Project、Postman Collection
- **ZIP 下載**：所有產生的檔案打包成 ZIP 直接下載
- **5 步驟精靈介面**：引導式表單，逐步填寫服務定義

---

## 支援的框架

### SOAP
| 框架 | 語言 |
|------|------|
| Spring-WS | Java |
| Apache CXF | Java |
| spyne | Python |
| soap (npm) | Node.js |
| CoreWCF | C# |
| SoapServer | PHP |
| net/http + WSDL | Go |

### REST
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

## 快速開始

### 需求環境

- Python 3.10+
- Node.js 18+
- npm

### 一鍵啟動（Windows）

直接雙擊 **`start.bat`** 即可。腳本會自動：
1. 檢查 Python 與 Node.js 是否安裝
2. 安裝後端與前端所需套件（首次執行需等待）
3. 開啟後端（port 8000）與前端（port 5173）服務
4. 自動在瀏覽器開啟 `http://localhost:5173`

**停止服務**：雙擊 **`stop.bat`**，會自動關閉所有相關行程。

> 若 Windows 顯示安全性警告，請點選「更多資訊」→「仍要執行」。

### 手動啟動

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

## 使用說明

### Step 1 — Basic Info（基本資料）

填寫服務的基本設定：

| 欄位 | 說明 | 範例 |
|------|------|------|
| Service Name | 服務名稱 | `UserService` |
| Service Type | 服務類型 | SOAP / REST / BOTH |
| Namespace | XML 命名空間（SOAP 必填） | `http://example.com/service` |
| Description | 服務描述 | 選填 |
| Version | 版本號 | `1.0` |

### Step 2 — Methods（方法定義）

新增服務的操作方法。每個方法可設定：

- **Name**：方法名稱（如 `getUser`）
- **Return Type**：回傳型別（如 `User`、`string`、`void`）
- **HTTP Method**：GET / POST / PUT / DELETE / PATCH（REST 模式）
- **Path**：URL 路徑，路徑參數用 `{paramName}`（如 `/users/{userId}`）
- **Parameters**：參數列表，每個參數設定名稱、型別、是否必填、位置（query / path / body / header）

**支援的型別**：`string`、`int`、`float`、`boolean`、`date`、`datetime`，以及在 Step 3 定義的 Model 名稱。

### Step 3 — Data Models（資料模型）

定義複雜型別。每個 Model 可包含多個 Field，每個 Field 設定名稱、型別、是否必填。

範例：

```
Model: User
  - id: int (required)
  - name: string (required)
  - email: string (optional)
  - active: boolean (required)
```

### Step 4 — Frameworks（選擇框架）

勾選想要產生的輸出框架。根據 Step 1 選擇的服務類型，會自動篩選顯示相應的 SOAP 或 REST 框架。

### Step 5 — Download（下載）

**下載專案代碼**：每個勾選的框架各有一個下載按鈕，點擊後下載對應語言的完整專案 ZIP。

**下載測試檔案**：選擇要輸出的測試格式，點擊下載：

| 格式 | 說明 | 用途 |
|------|------|------|
| SOAP XML Envelopes | 每個 method 的 SOAP 1.1 與 1.2 請求範本 | cURL、Insomnia、任何 HTTP 工具 |
| SoapUI Project | 可直接匯入 SoapUI 5.x 的 `.xml` | SoapUI 測試 |
| Postman Collection | Postman Collection v2.1 + Environment | Postman 測試 |

---

## API 文件

後端提供 3 個端點：

### `GET /api/frameworks`

取得所有支援的框架清單。

**回應範例：**
```json
{
  "soap": [
    {"id": "soap-java-spring-ws", "label": "Java (Spring-WS)"},
    ...
  ],
  "rest": [
    {"id": "rest-python-fastapi", "label": "Python (FastAPI)"},
    ...
  ]
}
```

### `POST /api/generate`

產生指定框架的專案代碼，回傳 ZIP 檔案。

**Request Body：**
```json
{
  "service": {
    "service_name": "UserService",
    "service_type": "REST",
    "namespace": "http://example.com/userservice",
    "version": "1.0",
    "methods": [
      {
        "name": "getUser",
        "http_method": "GET",
        "path": "/users/{userId}",
        "return_type": "User",
        "parameters": [
          {"name": "userId", "type": "int", "required": true, "location": "path"}
        ]
      }
    ],
    "models": [
      {
        "name": "User",
        "fields": [
          {"name": "id", "type": "int", "required": true},
          {"name": "name", "type": "string", "required": true}
        ]
      }
    ]
  },
  "framework": "rest-python-fastapi"
}
```

**回應：** `application/zip`

### `POST /api/generate-tests`

產生測試格式檔案，回傳 ZIP 檔案。

**Request Body：**
```json
{
  "service": { ...同上... },
  "test_types": ["soap-xml", "soapui", "postman"]
}
```

**`test_types` 可選值：** `soap-xml`、`soapui`、`postman`

---

## 執行測試

### 後端測試（pytest）

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

測試涵蓋範圍：
- **test_models.py** — Pydantic 資料模型驗證（50 個測試）
- **test_api.py** — FastAPI 端點整合測試，包含對 21 種框架全部驗證（60 個測試）
- **test_generators_soap.py** — 7 個 SOAP 生成器（98 個測試）
- **test_generators_rest.py** — 14 個 REST 生成器（159 個測試）
- **test_test_generators.py** — 3 個測試格式生成器（90 個測試）

共 **407 個測試**，全部通過。

### 前端測試（Vitest）

```bash
cd frontend
npm install
npm test
```

測試涵蓋範圍：
- **App.test.jsx** — 精靈導覽、步驟切換、API 呼叫
- **BasicInfo.test.jsx** — 表單欄位渲染與狀態更新
- **MethodBuilder.test.jsx** — 動態新增/刪除方法與參數
- **ModelBuilder.test.jsx** — 動態新增/刪除模型與欄位
- **FrameworkSelector.test.jsx** — 框架勾選、依服務類型篩選
- **StepIndicator.test.jsx** — 步驟指示器狀態
- **DownloadPanel.test.jsx** — 下載按鈕、loading 狀態、錯誤處理

共 **120 個測試**。

---

## 專案結構

```
webservices/
├── backend/
│   ├── main.py                      # FastAPI 主程式
│   ├── models.py                    # Pydantic 資料模型
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── generators/
│   │   ├── __init__.py              # get_generator() 工廠函式
│   │   ├── base.py                  # BaseGenerator 抽象類別
│   │   ├── soap/                    # 7 個 SOAP 生成器
│   │   └── rest/                    # 14 個 REST 生成器
│   ├── test_generators/
│   │   ├── soap_xml.py              # SOAP XML Envelope 生成器
│   │   ├── soapui_project.py        # SoapUI Project 生成器
│   │   └── postman_collection.py    # Postman Collection 生成器
│   └── tests/                       # pytest 測試
│       ├── conftest.py
│       ├── test_models.py
│       ├── test_api.py
│       ├── test_generators_soap.py
│       ├── test_generators_rest.py
│       └── test_test_generators.py
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── vitest.config.js
    ├── index.html
    └── src/
        ├── App.jsx                  # 5 步驟精靈控制器
        ├── App.css
        ├── main.jsx
        ├── components/
        │   ├── BasicInfo.jsx
        │   ├── MethodBuilder.jsx
        │   ├── ModelBuilder.jsx
        │   ├── FrameworkSelector.jsx
        │   ├── DownloadPanel.jsx
        │   └── StepIndicator.jsx
        └── tests/                   # Vitest 測試
```

---

## 新增自訂生成器

1. 在 `backend/generators/soap/` 或 `backend/generators/rest/` 建立新 Python 檔案
2. 繼承 `BaseGenerator` 並實作 `generate() -> Dict[str, str]`（key = 檔案路徑，value = 檔案內容）
3. 在 `backend/generators/__init__.py` 的 `GENERATORS` dict 加入新的 framework ID
4. 在 `backend/main.py` 的 `/api/frameworks` 回應中加入對應的 label
