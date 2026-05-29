import React, { useState, useEffect } from 'react'
import axios from 'axios'
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

export default function App() {
  const [step, setStep] = useState(1)
  const [service, setService] = useState(initialService)
  const [frameworks, setFrameworks] = useState({ soap: [], rest: [] })
  const [selectedFrameworks, setSelectedFrameworks] = useState([])
  const [frameworksError, setFrameworksError] = useState(null)

  useEffect(() => {
    axios.get('/api/frameworks')
      .then(res => setFrameworks(res.data))
      .catch(() => setFrameworksError('Failed to load frameworks from server.'))
  }, [])

  const totalSteps = 5

  const handleNext = () => {
    if (step < totalSteps) setStep(s => s + 1)
  }

  const handlePrev = () => {
    if (step > 1) setStep(s => s - 1)
  }

  const stepLabels = ['Basic Info', 'Methods', 'Data Models', 'Frameworks', 'Download']

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
        <h1>Web Services Generator</h1>
        <p className="app-subtitle">Define your service and generate production-ready code</p>
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
          &larr; Previous
        </button>

        {step < totalSteps && (
          <button
            className="btn btn-primary"
            onClick={handleNext}
          >
            Next &rarr;
          </button>
        )}
      </div>
    </div>
  )
}
