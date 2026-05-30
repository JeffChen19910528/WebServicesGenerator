import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { LanguageProvider, useLanguage } from './i18n/LanguageContext.jsx'
import StepIndicator from './components/StepIndicator.jsx'
import BasicInfo from './components/BasicInfo.jsx'
import MethodBuilder from './components/MethodBuilder.jsx'
import ModelBuilder from './components/ModelBuilder.jsx'
import FrameworkSelector from './components/FrameworkSelector.jsx'
import DownloadPanel from './components/DownloadPanel.jsx'

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

  const handleNext = () => {
    if (step < totalSteps) setStep(s => s + 1)
  }

  const handlePrev = () => {
    if (step > 1) setStep(s => s - 1)
  }

  const stepLabels = t('stepLabels')

  const renderStep = () => {
    switch (step) {
      case 1:
        return <BasicInfo service={service} setService={setService} />
      case 2:
        return <MethodBuilder service={service} setService={setService} />
      case 3:
        return <ModelBuilder service={service} setService={setService} />
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
      default:
        return null
    }
  }

  return (
    <div className="app-container">
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
            >
              EN
            </button>
            <span className="lang-divider">|</span>
            <button
              className={`lang-btn${lang === 'zh-TW' ? ' active' : ''}`}
              onClick={() => setLang('zh-TW')}
              aria-label="切換為繁體中文"
            >
              繁中
            </button>
          </div>
        </div>
      </header>

      <StepIndicator currentStep={step} totalSteps={totalSteps} labels={stepLabels} />

      <main className="step-content">
        {renderStep()}
      </main>

      <div className="nav-buttons">
        <button
          className="btn btn-secondary"
          onClick={handlePrev}
          disabled={step === 1}
        >
          {t('prev')}
        </button>

        {step < totalSteps && (
          <button
            className="btn btn-primary"
            onClick={handleNext}
          >
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
