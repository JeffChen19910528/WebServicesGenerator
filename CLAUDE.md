# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 啟動方式

**後端（FastAPI）：**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**前端（React + Vite）：**
```bash
cd frontend
npm install
npm run dev   # 預設 http://localhost:5173
```

## 專案架構

```
webservices/
├── backend/
│   ├── main.py                  # FastAPI 主程式，兩個端點：/api/generate、/api/generate-tests
│   ├── models.py                # Pydantic 資料模型：ServiceDefinition、Method、Parameter、ModelDef
│   ├── generators/
│   │   ├── __init__.py          # get_generator(framework, service) 工廠函式
│   │   ├── base.py              # BaseGenerator 抽象類別
│   │   ├── soap/                # 7 個 SOAP 生成器（Java Spring-WS/CXF、Python spyne、Node.js、C# WCF、PHP、Go）
│   │   └── rest/                # 14 個 REST 生成器（Java、Python、Node.js、C#、PHP、Go、Ruby）
│   └── test_generators/
│       ├── soap_xml.py          # 產生 SOAP 1.1/1.2 XML envelope 範本
│       ├── soapui_project.py    # 產生 SoapUI 5.x project XML
│       └── postman_collection.py # 產生 Postman Collection v2.1 JSON
└── frontend/
    └── src/
        ├── App.jsx              # 5 步驟精靈控制器
        └── components/
            ├── BasicInfo.jsx    # Step 1：服務基本資料
            ├── MethodBuilder.jsx # Step 2：動態新增方法與參數
            ├── ModelBuilder.jsx  # Step 3：動態新增資料模型
            ├── FrameworkSelector.jsx # Step 4：選擇輸出框架
            └── DownloadPanel.jsx # Step 5：下載專案 ZIP 與測試檔
```

## API 端點

| 端點 | 說明 |
|------|------|
| `GET /api/frameworks` | 回傳所有支援的框架清單 |
| `POST /api/generate` | body: `{service, framework}` → 回傳專案 ZIP |
| `POST /api/generate-tests` | body: `{service, test_types[]}` → 回傳測試檔 ZIP |

## 新增生成器

1. 在 `backend/generators/soap/` 或 `rest/` 建立新檔案，繼承 `BaseGenerator`
2. 實作 `generate() -> Dict[str, str]`（key = 檔案路徑，value = 檔案內容）
3. 在 `backend/generators/__init__.py` 的 `GENERATORS` dict 加入新的 framework id

## 行為準則

1. **先思考再行動**：執行任何任務前，先規劃好步驟與方法，確認方向正確後再開始執行。
2. **保持簡單**：優先選擇簡單直接的解法，避免過度設計或不必要的複雜化。
3. **使用繁體中文回答**：所有回應一律使用繁體中文。
