import React from 'react'
import { useLanguage } from '../i18n/LanguageContext.jsx'

export default function FrameworkSelector({ frameworks, selected, onChange, service, error }) {
  const { t } = useLanguage()
  const showSoap = service.service_type === 'SOAP' || service.service_type === 'BOTH'
  const showRest = service.service_type === 'REST' || service.service_type === 'BOTH'

  const toggle = (id) => {
    if (selected.includes(id)) {
      onChange(selected.filter(s => s !== id))
    } else {
      onChange([...selected, id])
    }
  }

  const renderGroup = (title, items) => {
    if (!items || items.length === 0) return null
    return (
      <div className="framework-group">
        <h3 className="framework-group-title">{title}</h3>
        <div className="framework-options">
          {items.map(fw => (
            <label key={fw.id} className={`framework-card ${selected.includes(fw.id) ? 'selected' : ''}`}>
              <input
                type="checkbox"
                checked={selected.includes(fw.id)}
                onChange={() => toggle(fw.id)}
              />
              <div className="framework-card-content">
                <span className="framework-name">{fw.label}</span>
                <span className="framework-id">{fw.id}</span>
              </div>
            </label>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="card-title">{t('frameworksTitle')}</h2>
      <p className="card-description">{t('frameworksDesc')}</p>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      {!error && frameworks.soap.length === 0 && frameworks.rest.length === 0 && (
        <div className="alert alert-info">{t('loadingFrameworks')}</div>
      )}

      {showSoap && renderGroup(t('soapFrameworks'), frameworks.soap)}
      {showRest && renderGroup(t('restFrameworks'), frameworks.rest)}

      {selected.length > 0 && (
        <div className="selected-summary">
          <strong>{t('selected')}:</strong> {selected.join(', ')}
        </div>
      )}
    </div>
  )
}
