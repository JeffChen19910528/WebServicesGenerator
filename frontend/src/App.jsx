import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { LanguageProvider, useLanguage } from './i18n/LanguageContext.jsx'
import StepIndicator from './components/StepIndicator.jsx'
import BasicInfo from './components/BasicInfo.jsx'
import MethodBuilder from './components/MethodBuilder.jsx'
import ModelBuilder from './components/ModelBuilder.jsx'
import FrameworkSelector from './components/FrameworkSelector.jsx'
import DownloadPanel from './components/DownloadPanel.jsx'
import DatabaseWizard from './components/DatabaseWizard.jsx'

const initialService = {
  service_name: '',
  service_type: 'REST',
  namespace: 'http://example.com/service',
  description: '',
  version: '1.0',
  methods: [],
  models: []
}

function AppContent() {
  const { lang, setLang, t } = useLanguage()
  const [mode, setMode] = useState(null) // null | 'manual' | 'database'
  const [step, setStep] = useState(1)
  const [service, setService] = useState(initialService)
  const [frameworks, setFrameworks] = useState({ soap: [], rest: [] })
  const [selectedFrameworks, setSelectedFrameworks] = useState([])
  const [frameworksError, setFrameworksError] = useState(null)

  useEffect(() => {
    axios.get('/api/frameworks')
      .then(res => setFrameworks(res.data))
      .catch(() => setFrameworksError(t('failedToLoadFrameworks')))
  }, [])

  const totalSteps = 5

  const handleNext = () => { if (step < totalSteps) setStep(s => s + 1) }
  const handlePrev = () => { if (step > 1) setStep(s => s - 1) }

  const stepLabels = t('stepLabels')

  const handleBackToHome = () => {
    setMode(null)
    setStep(1)
    setService(initialService)
    setSelectedFrameworks([])
  }

  const renderStep = () => {
    switch (step) {
      case 1: return <BasicInfo service={service} setService={setService} />
      case 2: return <MethodBuilder service={service} setService={setService} />
      case 3: return <ModelBuilder service={service} setService={setService} />
      case 4:
        return (
          <FrameworkSelector
            frameworks={frameworks}
            selected={selectedFrameworks}
            onChange={setSelectedFrameworks}
            service={service}
            error={frameworksError}
          />
        )
      case 5:
        return (
          <DownloadPanel
            service={service}
            selectedFrameworks={selectedFrameworks}
            frameworks={frameworks}
          />
        )
      default: return null
    }
  }

  const renderHeader = () => (
    <header className="app-header">
      <div className="app-header-content">
        <div>
          <h1>{t('appTitle')}</h1>
          <p className="app-subtitle">{t('appSubtitle')}</p>
        </div>
        <div className="lang-switcher">
          <button
            className={`lang-btn${lang === 'en' ? ' active' : ''}`}
            onClick={() => setLang('en')}
            aria-label="Switch to English"
          >EN</button>
          <span className="lang-divider">|</span>
          <button
            className={`lang-btn${lang === 'zh-TW' ? ' active' : ''}`}
            onClick={() => setLang('zh-TW')}
            aria-label="切換為繁體中文"
          >繁中</button>
        </div>
      </div>
    </header>
  )

  // Mode selection landing page
  if (mode === null) {
    return (
      <div className="app-container">
        {renderHeader()}
        <div className="mode-selector">
          <h2 className="mode-selector-title">
            {lang === 'zh-TW' ? '選擇建立方式' : 'Choose how to get started'}
          </h2>
          <p className="mode-selector-desc">
            {lang === 'zh-TW'
              ? '您可以手動定義服務，或直接從資料庫（MS SQL、MySQL、PostgreSQL、SQLite）自動產生。'
              : 'Manually define your service, or auto-generate from a database (MS SQL, MySQL, PostgreSQL, SQLite).'}
          </p>
          <div className="mode-cards">
            <button className="mode-card" onClick={() => setMode('manual')}>
              <div className="mode-card-icon">✏️</div>
              <div className="mode-card-body">
                <div className="mode-card-title">
                  {lang === 'zh-TW' ? '手動建立' : 'Manual Setup'}
                </div>
                <div className="mode-card-desc">
                  {lang === 'zh-TW'
                    ? '自行定義服務名稱、方法、參數與資料模型，完全客製化。'
                    : 'Define service name, methods, parameters and models from scratch.'}
                </div>
              </div>
              <span className="mode-card-arrow">→</span>
            </button>

            <button className="mode-card mode-card-db" onClick={() => setMode('database')}>
              <div className="mode-card-icon">🗄️</div>
              <div className="mode-card-body">
                <div className="mode-card-title">
                  {lang === 'zh-TW' ? '從資料庫匯入' : 'Import from Database'}
                </div>
                <div className="mode-card-desc">
                  {lang === 'zh-TW'
                    ? '連線到資料庫，選擇資料表，自動產生 CRUD Web Service。'
                    : 'Connect to a database, pick tables, and auto-generate CRUD web services.'}
                </div>
                <div className="mode-card-badge">MS SQL · MySQL · PostgreSQL · SQLite</div>
              </div>
              <span className="mode-card-arrow">→</span>
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (mode === 'database') {
    return (
      <div className="app-container">
        {renderHeader()}
        <DatabaseWizard frameworks={frameworks} onBack={handleBackToHome} />
      </div>
    )
  }

  // Manual mode
  return (
    <div className="app-container">
      {renderHeader()}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <button className="btn btn-secondary btn-sm" onClick={handleBackToHome}>
          ← {lang === 'zh-TW' ? '返回首頁' : 'Back to Home'}
        </button>
      </div>
      <StepIndicator currentStep={step} totalSteps={totalSteps} labels={stepLabels} />
      <main className="step-content">
        {renderStep()}
      </main>
      <div className="nav-buttons">
        <button className="btn btn-secondary" onClick={handlePrev} disabled={step === 1}>
          {t('prev')}
        </button>
        {step < totalSteps && (
          <button className="btn btn-primary" onClick={handleNext}>
            {t('next')}
          </button>
        )}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  )
}
