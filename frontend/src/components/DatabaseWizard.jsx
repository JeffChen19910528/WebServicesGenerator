import React, { useState } from 'react'
import axios from 'axios'
import { useLanguage } from '../i18n/LanguageContext.jsx'
import FrameworkSelector from './FrameworkSelector.jsx'
import DownloadPanel from './DownloadPanel.jsx'
import StepIndicator from './StepIndicator.jsx'

const ALL_OPS = ['getAll', 'getById', 'create', 'update', 'delete']

const OP_LABELS = {
  getAll:   { en: 'Get All',    zh: '查詢全部' },
  getById:  { en: 'Get By ID',  zh: '依 ID 查詢' },
  create:   { en: 'Create',     zh: '新增' },
  update:   { en: 'Update',     zh: '更新' },
  delete:   { en: 'Delete',     zh: '刪除' },
}

const OP_METHOD = {
  getAll: 'GET', getById: 'GET', create: 'POST', update: 'PUT', delete: 'DELETE'
}

const initialConn = {
  server: '', port: '', database: '',
  username: '', password: '', auth_type: 'sql',
}

export default function DatabaseWizard({ frameworks, onBack }) {
  const { lang, t } = useLanguage()
  const dt = (key) => t('db_' + key) || key

  const [step, setStep] = useState(1)
  const [conn, setConn] = useState(initialConn)
  const [connecting, setConnecting] = useState(false)
  const [connError, setConnError] = useState(null)

  const [tables, setTables] = useState([])
  const [selectedTables, setSelectedTables] = useState([])

  const [schema, setSchema] = useState({})
  const [operations, setOperations] = useState({})
  const [loadingSchema, setLoadingSchema] = useState(false)

  const [serviceName, setServiceName] = useState('')
  const [serviceType, setServiceType] = useState('REST')

  const [generating, setGenerating] = useState(false)
  const [generatedService, setGeneratedService] = useState(null)
  const [genError, setGenError] = useState(null)

  const [selectedFrameworks, setSelectedFrameworks] = useState([])

  const stepLabels = lang === 'zh-TW'
    ? ['連線設定', '選擇資料表', '操作設定', '選擇框架', '下載']
    : ['Connection', 'Select Tables', 'Operations', 'Frameworks', 'Download']

  // ── Step 1: Connect ──────────────────────────────────────────
  async function handleConnect() {
    if (!conn.server || !conn.database) {
      setConnError(lang === 'zh-TW' ? '請填寫伺服器位址與資料庫名稱' : 'Server and database are required')
      return
    }
    setConnecting(true)
    setConnError(null)
    try {
      const payload = {
        server: conn.server,
        port: conn.port ? parseInt(conn.port) : null,
        database: conn.database,
        username: conn.auth_type === 'sql' ? conn.username : null,
        password: conn.auth_type === 'sql' ? conn.password : null,
        auth_type: conn.auth_type,
      }
      const res = await axios.post('/api/database/connect', payload)
      setTables(res.data.tables)
      setSelectedTables([])
      setStep(2)
    } catch (e) {
      setConnError(e.response?.data?.detail || (lang === 'zh-TW' ? '連線失敗，請確認連線資訊' : 'Connection failed'))
    } finally {
      setConnecting(false)
    }
  }

  // ── Step 2: Table selection ───────────────────────────────────
  function toggleTable(fullName) {
    setSelectedTables(prev =>
      prev.includes(fullName) ? prev.filter(t => t !== fullName) : [...prev, fullName]
    )
  }

  function toggleAllTables() {
    if (selectedTables.length === tables.length) {
      setSelectedTables([])
    } else {
      setSelectedTables(tables.map(t => t.full_name))
    }
  }

  async function handleLoadSchema() {
    if (selectedTables.length === 0) {
      return
    }
    setLoadingSchema(true)
    try {
      const payload = {
        server: conn.server,
        port: conn.port ? parseInt(conn.port) : null,
        database: conn.database,
        username: conn.auth_type === 'sql' ? conn.username : null,
        password: conn.auth_type === 'sql' ? conn.password : null,
        auth_type: conn.auth_type,
        tables: selectedTables,
      }
      const res = await axios.post('/api/database/schema', payload)
      setSchema(res.data.schema)
      const defaultOps = {}
      selectedTables.forEach(t => { defaultOps[t] = [...ALL_OPS] })
      setOperations(defaultOps)
      setStep(3)
    } catch (e) {
      setConnError(e.response?.data?.detail || 'Schema load failed')
    } finally {
      setLoadingSchema(false)
    }
  }

  // ── Step 3: Operations ────────────────────────────────────────
  function toggleOp(tableName, op) {
    setOperations(prev => {
      const ops = prev[tableName] || []
      return {
        ...prev,
        [tableName]: ops.includes(op) ? ops.filter(o => o !== op) : [...ops, op],
      }
    })
  }

  function toggleAllOps(tableName) {
    setOperations(prev => {
      const ops = prev[tableName] || []
      return { ...prev, [tableName]: ops.length === ALL_OPS.length ? [] : [...ALL_OPS] }
    })
  }

  async function handleGenerateService() {
    if (!serviceName.trim()) {
      setGenError(lang === 'zh-TW' ? '請輸入服務名稱' : 'Service name is required')
      return
    }
    setGenerating(true)
    setGenError(null)
    try {
      const payload = {
        server: conn.server,
        port: conn.port ? parseInt(conn.port) : null,
        database: conn.database,
        username: conn.auth_type === 'sql' ? conn.username : null,
        password: conn.auth_type === 'sql' ? conn.password : null,
        auth_type: conn.auth_type,
        tables: selectedTables,
        operations,
        service_name: serviceName.trim(),
        service_type: serviceType,
        namespace: `http://example.com/${serviceName.trim().toLowerCase()}`,
      }
      const res = await axios.post('/api/database/generate-service', payload)
      setGeneratedService(res.data)
      setStep(4)
    } catch (e) {
      setGenError(e.response?.data?.detail || 'Generation failed')
    } finally {
      setGenerating(false)
    }
  }

  // ── Render helpers ────────────────────────────────────────────
  function renderStep1() {
    return (
      <div>
        <div className="section-header">
          <div>
            <div className="section-title">{dt('connectionTitle')}</div>
            <div className="section-description">{dt('connectionDesc')}</div>
          </div>
        </div>

        <div className="card">
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                {dt('server')} <span className="required">*</span>
              </label>
              <input
                className="form-input"
                placeholder={dt('serverPlaceholder')}
                value={conn.server}
                onChange={e => setConn(c => ({ ...c, server: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <label className="form-label">{dt('port')}</label>
              <input
                className="form-input"
                placeholder="1433"
                value={conn.port}
                onChange={e => setConn(c => ({ ...c, port: e.target.value }))}
                type="number"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              {dt('database')} <span className="required">*</span>
            </label>
            <input
              className="form-input"
              placeholder={dt('databasePlaceholder')}
              value={conn.database}
              onChange={e => setConn(c => ({ ...c, database: e.target.value }))}
            />
          </div>

          <div className="form-group">
            <label className="form-label">{dt('authType')}</label>
            <div className="radio-group">
              <label className="radio-label">
                <input type="radio" name="auth_type" value="sql"
                  checked={conn.auth_type === 'sql'}
                  onChange={() => setConn(c => ({ ...c, auth_type: 'sql' }))} />
                <span className="radio-text">{dt('authSQL')}</span>
              </label>
              <label className="radio-label">
                <input type="radio" name="auth_type" value="windows"
                  checked={conn.auth_type === 'windows'}
                  onChange={() => setConn(c => ({ ...c, auth_type: 'windows' }))} />
                <span className="radio-text">{dt('authWindows')}</span>
              </label>
            </div>
          </div>

          {conn.auth_type === 'sql' && (
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">{dt('username')}</label>
                <input
                  className="form-input"
                  placeholder={dt('usernamePlaceholder')}
                  value={conn.username}
                  onChange={e => setConn(c => ({ ...c, username: e.target.value }))}
                  autoComplete="username"
                />
              </div>
              <div className="form-group">
                <label className="form-label">{dt('password')}</label>
                <input
                  className="form-input"
                  type="password"
                  placeholder="••••••••"
                  value={conn.password}
                  onChange={e => setConn(c => ({ ...c, password: e.target.value }))}
                  autoComplete="current-password"
                />
              </div>
            </div>
          )}

          {connError && <div className="alert alert-error">{connError}</div>}

          <button className="btn btn-primary" onClick={handleConnect} disabled={connecting}>
            {connecting && <span className="spinner" />}
            {connecting ? dt('connecting') : dt('connect')}
          </button>
        </div>
      </div>
    )
  }

  function renderStep2() {
    const allSelected = selectedTables.length === tables.length && tables.length > 0
    return (
      <div>
        <div className="section-header">
          <div>
            <div className="section-title">{dt('selectTablesTitle')}</div>
            <div className="section-description">
              {dt('selectTablesDesc')} &mdash; {lang === 'zh-TW' ? `已連線至 ${conn.database}` : `Connected to ${conn.database}`}
            </div>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={toggleAllTables}>
            {allSelected ? dt('deselectAll') : dt('selectAll')}
          </button>
        </div>

        {tables.length === 0 ? (
          <div className="empty-state">{dt('noTables')}</div>
        ) : (
          <div className="db-table-grid">
            {tables.map(tbl => {
              const selected = selectedTables.includes(tbl.full_name)
              return (
                <label key={tbl.full_name} className={`db-table-card${selected ? ' selected' : ''}`}>
                  <input
                    type="checkbox"
                    checked={selected}
                    onChange={() => toggleTable(tbl.full_name)}
                  />
                  <div className="db-table-card-content">
                    <span className="db-table-name">{tbl.table_name}</span>
                    {tbl.schema !== 'dbo' && (
                      <span className="db-table-schema">{tbl.schema}</span>
                    )}
                  </div>
                </label>
              )
            })}
          </div>
        )}

        {selectedTables.length > 0 && (
          <div className="alert alert-info" style={{ marginTop: '1rem' }}>
            {lang === 'zh-TW'
              ? `已選擇 ${selectedTables.length} 個資料表`
              : `${selectedTables.length} table(s) selected`}
          </div>
        )}

        {connError && <div className="alert alert-error" style={{ marginTop: '0.5rem' }}>{connError}</div>}

        <div className="nav-buttons" style={{ marginTop: '1.5rem' }}>
          <button className="btn btn-secondary" onClick={() => setStep(1)}>{t('prev')}</button>
          <button
            className="btn btn-primary"
            onClick={handleLoadSchema}
            disabled={selectedTables.length === 0 || loadingSchema}
          >
            {loadingSchema && <span className="spinner" />}
            {loadingSchema ? dt('loadingSchema') : dt('nextOps')}
          </button>
        </div>
      </div>
    )
  }

  function renderStep3() {
    return (
      <div>
        <div className="section-header">
          <div>
            <div className="section-title">{dt('opsTitle')}</div>
            <div className="section-description">{dt('opsDesc')}</div>
          </div>
        </div>

        <div className="card">
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                {t('serviceName')} <span className="required">*</span>
              </label>
              <input
                className="form-input"
                placeholder={lang === 'zh-TW' ? '例如 ProductService' : 'e.g. ProductService'}
                value={serviceName}
                onChange={e => setServiceName(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">{t('serviceType')}</label>
              <div className="radio-group">
                {['REST', 'SOAP', 'BOTH'].map(st => (
                  <label key={st} className="radio-label">
                    <input type="radio" name="svcType" value={st}
                      checked={serviceType === st}
                      onChange={() => setServiceType(st)} />
                    <span className="radio-text">{st}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>

        {selectedTables.map(fullName => {
          const display = fullName.split('.').pop()
          const cols = schema[fullName] || []
          const ops = operations[fullName] || []
          const allChecked = ops.length === ALL_OPS.length

          return (
            <div key={fullName} className="card" style={{ marginBottom: '1rem' }}>
              <div className="card-header">
                <div>
                  <div className="card-subtitle">{display}</div>
                  <div className="db-col-preview">
                    {cols.map(c => (
                      <span key={c.name} className={`db-col-tag${c.is_primary_key ? ' pk' : ''}`}>
                        {c.name}
                        <em>{c.sql_type}</em>
                        {c.is_primary_key && <strong>PK</strong>}
                      </span>
                    ))}
                  </div>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={() => toggleAllOps(fullName)}>
                  {allChecked ? dt('deselectAll') : dt('selectAll')}
                </button>
              </div>

              <div className="db-ops-grid">
                {ALL_OPS.map(op => {
                  const checked = ops.includes(op)
                  const opLabel = OP_LABELS[op][lang === 'zh-TW' ? 'zh' : 'en']
                  return (
                    <label key={op} className={`db-op-card${checked ? ' selected' : ''}`}>
                      <input type="checkbox" checked={checked}
                        onChange={() => toggleOp(fullName, op)} />
                      <div className="db-op-info">
                        <span className={`db-op-method db-op-${OP_METHOD[op].toLowerCase()}`}>
                          {OP_METHOD[op]}
                        </span>
                        <span className="db-op-label">{opLabel}</span>
                      </div>
                    </label>
                  )
                })}
              </div>
            </div>
          )
        })}

        {genError && <div className="alert alert-error">{genError}</div>}

        <div className="nav-buttons">
          <button className="btn btn-secondary" onClick={() => setStep(2)}>{t('prev')}</button>
          <button className="btn btn-primary" onClick={handleGenerateService} disabled={generating}>
            {generating && <span className="spinner" />}
            {generating ? dt('generating') : dt('generateService')}
          </button>
        </div>
      </div>
    )
  }

  function renderStep4() {
    return (
      <div>
        <div className="section-header">
          <div>
            <div className="section-title">{t('frameworksTitle')}</div>
            <div className="section-description">{t('frameworksDesc')}</div>
          </div>
        </div>
        <FrameworkSelector
          frameworks={frameworks}
          selected={selectedFrameworks}
          onChange={setSelectedFrameworks}
          service={generatedService}
        />
        <div className="nav-buttons">
          <button className="btn btn-secondary" onClick={() => setStep(3)}>{t('prev')}</button>
          <button
            className="btn btn-primary"
            onClick={() => setStep(5)}
            disabled={selectedFrameworks.length === 0}
          >
            {t('next')}
          </button>
        </div>
      </div>
    )
  }

  function renderStep5() {
    return (
      <div>
        <DownloadPanel
          service={generatedService}
          selectedFrameworks={selectedFrameworks}
          frameworks={frameworks}
        />
        <div className="nav-buttons">
          <button className="btn btn-secondary" onClick={() => setStep(4)}>{t('prev')}</button>
        </div>
      </div>
    )
  }

  const renderContent = () => {
    switch (step) {
      case 1: return renderStep1()
      case 2: return renderStep2()
      case 3: return renderStep3()
      case 4: return renderStep4()
      case 5: return renderStep5()
      default: return null
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <button className="btn btn-secondary btn-sm" onClick={onBack}>
          ← {lang === 'zh-TW' ? '返回首頁' : 'Back to Home'}
        </button>
        <span style={{ color: '#64748b', fontSize: '0.875rem' }}>
          {lang === 'zh-TW' ? 'MS SQL Server 資料庫匯入' : 'Import from MS SQL Server'}
        </span>
      </div>

      <StepIndicator currentStep={step} totalSteps={5} labels={stepLabels} />

      <main className="step-content">
        {renderContent()}
      </main>
    </div>
  )
}
