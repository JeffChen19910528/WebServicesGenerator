import React from 'react'
import { useLanguage } from '../i18n/LanguageContext.jsx'

const PRIMITIVE_TYPES = ['string', 'int', 'float', 'boolean', 'date', 'datetime']
const HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
const PARAM_LOCATIONS = ['query', 'path', 'body', 'header']

const blankParameter = () => ({
  name: '',
  type: 'string',
  required: false,
  location: 'query'
})

const blankMethod = () => ({
  name: '',
  description: '',
  parameters: [],
  return_type: 'string',
  http_method: 'GET',
  path: '/'
})

export default function MethodBuilder({ service, setService }) {
  const { t } = useLanguage()
  const isRestLike = service.service_type === 'REST' || service.service_type === 'BOTH'
  const modelNames = service.models.map(m => m.name).filter(Boolean)
  const allTypes = [...PRIMITIVE_TYPES, ...modelNames]

  const updateMethod = (index, field, value) => {
    setService(prev => {
      const methods = prev.methods.map((m, i) =>
        i === index ? { ...m, [field]: value } : m
      )
      return { ...prev, methods }
    })
  }

  const addMethod = () => {
    setService(prev => ({
      ...prev,
      methods: [...prev.methods, blankMethod()]
    }))
  }

  const removeMethod = (index) => {
    setService(prev => ({
      ...prev,
      methods: prev.methods.filter((_, i) => i !== index)
    }))
  }

  const addParameter = (methodIndex) => {
    setService(prev => {
      const methods = prev.methods.map((m, i) => {
        if (i !== methodIndex) return m
        return { ...m, parameters: [...m.parameters, blankParameter()] }
      })
      return { ...prev, methods }
    })
  }

  const updateParameter = (methodIndex, paramIndex, field, value) => {
    setService(prev => {
      const methods = prev.methods.map((m, i) => {
        if (i !== methodIndex) return m
        const parameters = m.parameters.map((p, j) =>
          j === paramIndex ? { ...p, [field]: value } : p
        )
        return { ...m, parameters }
      })
      return { ...prev, methods }
    })
  }

  const removeParameter = (methodIndex, paramIndex) => {
    setService(prev => {
      const methods = prev.methods.map((m, i) => {
        if (i !== methodIndex) return m
        return { ...m, parameters: m.parameters.filter((_, j) => j !== paramIndex) }
      })
      return { ...prev, methods }
    })
  }

  return (
    <div>
      <div className="section-header">
        <div>
          <h2 className="section-title">{t('methodsTitle')}</h2>
          <p className="section-description">{t('methodsDesc')}</p>
        </div>
        <button className="btn btn-primary" onClick={addMethod}>
          {t('addMethod')}
        </button>
      </div>

      {service.methods.length === 0 && (
        <div className="empty-state">
          <p>{t('noMethods')}</p>
        </div>
      )}

      {service.methods.map((method, methodIndex) => (
        <div key={methodIndex} className="card method-card">
          <div className="card-header">
            <h3 className="card-subtitle">{t('method')} {methodIndex + 1}</h3>
            <button
              className="btn btn-danger btn-sm"
              onClick={() => removeMethod(methodIndex)}
            >
              {t('removeMethod')}
            </button>
          </div>

          <div className="form-row">
            <div className="form-group form-group-flex">
              <label className="form-label">{t('methodName')}</label>
              <input
                type="text"
                className="form-input"
                placeholder={t('methodNamePlaceholder')}
                value={method.name}
                onChange={e => updateMethod(methodIndex, 'name', e.target.value)}
              />
            </div>

            <div className="form-group form-group-flex">
              <label className="form-label">{t('returnType')}</label>
              <input
                type="text"
                className="form-input"
                placeholder={t('returnTypePlaceholder')}
                value={method.return_type}
                onChange={e => updateMethod(methodIndex, 'return_type', e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">{t('methodDesc')}</label>
            <input
              type="text"
              className="form-input"
              placeholder={t('methodDescPlaceholder')}
              value={method.description}
              onChange={e => updateMethod(methodIndex, 'description', e.target.value)}
            />
          </div>

          {isRestLike && (
            <div className="form-row">
              <div className="form-group form-group-flex">
                <label className="form-label">{t('httpMethod')}</label>
                <select
                  className="form-select"
                  value={method.http_method}
                  onChange={e => updateMethod(methodIndex, 'http_method', e.target.value)}
                >
                  {HTTP_METHODS.map(hm => (
                    <option key={hm} value={hm}>{hm}</option>
                  ))}
                </select>
              </div>

              <div className="form-group form-group-flex">
                <label className="form-label">{t('path')}</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder={t('pathPlaceholder')}
                  value={method.path}
                  onChange={e => updateMethod(methodIndex, 'path', e.target.value)}
                />
              </div>
            </div>
          )}

          <div className="params-section">
            <div className="params-header">
              <h4 className="params-title">{t('parameters')}</h4>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => addParameter(methodIndex)}
              >
                {t('addParameter')}
              </button>
            </div>

            {method.parameters.length === 0 && (
              <p className="empty-params">{t('noParameters')}</p>
            )}

            {method.parameters.map((param, paramIndex) => (
              <div key={paramIndex} className="param-row">
                <div className="param-fields">
                  <div className="form-group">
                    <label className="form-label form-label-sm">{t('paramName')}</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder={t('paramNamePlaceholder')}
                      value={param.name}
                      onChange={e => updateParameter(methodIndex, paramIndex, 'name', e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label form-label-sm">{t('paramType')}</label>
                    <select
                      className="form-select"
                      value={param.type}
                      onChange={e => updateParameter(methodIndex, paramIndex, 'type', e.target.value)}
                    >
                      {allTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>

                  {isRestLike && (
                    <div className="form-group">
                      <label className="form-label form-label-sm">{t('paramLocation')}</label>
                      <select
                        className="form-select"
                        value={param.location}
                        onChange={e => updateParameter(methodIndex, paramIndex, 'location', e.target.value)}
                      >
                        {PARAM_LOCATIONS.map(loc => (
                          <option key={loc} value={loc}>{loc}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  <div className="form-group form-group-checkbox">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={param.required}
                        onChange={e => updateParameter(methodIndex, paramIndex, 'required', e.target.checked)}
                      />
                      <span>{t('paramRequired')}</span>
                    </label>
                  </div>
                </div>

                <button
                  className="btn btn-danger btn-sm btn-icon"
                  onClick={() => removeParameter(methodIndex, paramIndex)}
                  title={t('removeParam')}
                >
                  &times;
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
