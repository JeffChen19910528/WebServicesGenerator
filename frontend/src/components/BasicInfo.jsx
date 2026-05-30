import React from 'react'
import { useLanguage } from '../i18n/LanguageContext.jsx'

export default function BasicInfo({ service, setService }) {
  const { t } = useLanguage()

  const update = (field, value) => {
    setService(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="card">
      <h2 className="card-title">{t('basicInfoTitle')}</h2>
      <p className="card-description">{t('basicInfoDesc')}</p>

      <div className="form-group">
        <label className="form-label" htmlFor="service_name">
          {t('serviceName')} <span className="required">*</span>
        </label>
        <input
          id="service_name"
          type="text"
          className="form-input"
          placeholder={t('serviceNamePlaceholder')}
          value={service.service_name}
          onChange={e => update('service_name', e.target.value)}
          required
        />
      </div>

      <div className="form-group">
        <label className="form-label">{t('serviceType')}</label>
        <div className="radio-group">
          {['SOAP', 'REST', 'BOTH'].map(type => (
            <label key={type} className="radio-label">
              <input
                type="radio"
                name="service_type"
                value={type}
                checked={service.service_type === type}
                onChange={() => update('service_type', type)}
              />
              <span className="radio-text">{type}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="namespace">{t('namespace')}</label>
        <input
          id="namespace"
          type="text"
          className="form-input"
          placeholder={t('namespacePlaceholder')}
          value={service.namespace}
          onChange={e => update('namespace', e.target.value)}
        />
        <p className="form-hint">{t('namespaceHint')}</p>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="description">{t('description')}</label>
        <textarea
          id="description"
          className="form-textarea"
          placeholder={t('descriptionPlaceholder')}
          value={service.description}
          onChange={e => update('description', e.target.value)}
          rows={4}
        />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="version">{t('version')}</label>
        <input
          id="version"
          type="text"
          className="form-input form-input-short"
          placeholder="1.0"
          value={service.version}
          onChange={e => update('version', e.target.value)}
        />
      </div>
    </div>
  )
}
