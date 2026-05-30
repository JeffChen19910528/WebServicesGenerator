import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import React from 'react'
import ModelBuilder from '../components/ModelBuilder'
import { LanguageProvider } from '../i18n/LanguageContext.jsx'
import { renderWithLang } from './testUtils'

const baseService = {
  service_name: 'TestService',
  service_type: 'REST',
  namespace: 'http://example.com/service',
  description: '',
  version: '1.0',
  methods: [],
  models: []
}

function renderWithState(initialService) {
  let currentService = { ...initialService, models: [...initialService.models] }
  const setService = vi.fn(updater => {
    currentService = typeof updater === 'function' ? updater(currentService) : updater
    rerender(
      <LanguageProvider>
        <ModelBuilder service={currentService} setService={setService} />
      </LanguageProvider>
    )
  })
  const { rerender } = render(
    <LanguageProvider>
      <ModelBuilder service={currentService} setService={setService} />
    </LanguageProvider>
  )
  return { setService, getService: () => currentService }
}

describe('ModelBuilder', () => {
  describe('empty state', () => {
    it('renders the Add Model button', () => {
      renderWithLang(<ModelBuilder service={baseService} setService={vi.fn()} />)
      expect(screen.getByRole('button', { name: /add model/i })).toBeInTheDocument()
    })

    it('shows empty state message when no models exist', () => {
      renderWithLang(<ModelBuilder service={baseService} setService={vi.fn()} />)
      expect(screen.getByText(/no data models defined/i)).toBeInTheDocument()
    })

    it('does not show any model card when models array is empty', () => {
      renderWithLang(<ModelBuilder service={baseService} setService={vi.fn()} />)
      expect(screen.queryByText(/model 1/i)).not.toBeInTheDocument()
    })
  })

  describe('adding models', () => {
    it('clicking Add Model makes a model card appear', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      expect(screen.getByText(/model 1/i)).toBeInTheDocument()
    })

    it('model card contains a Model Name input', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      expect(screen.getByPlaceholderText(/e\.g\. user/i)).toBeInTheDocument()
    })

    it('can type a model name into the model name input', () => {
      const { getService } = renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      fireEvent.change(screen.getByPlaceholderText(/e\.g\. user/i), {
        target: { value: 'UserProfile' }
      })
      expect(getService().models[0].name).toBe('UserProfile')
    })

    it('adding two models shows Model 1 and Model 2 headings', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      expect(screen.getByText(/model 1/i)).toBeInTheDocument()
      expect(screen.getByText(/model 2/i)).toBeInTheDocument()
    })

    it('new model card shows "No fields defined" placeholder', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      expect(screen.getByText(/no fields defined/i)).toBeInTheDocument()
    })
  })

  describe('removing models', () => {
    it('clicking Remove Model deletes the model card', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      expect(screen.getByText(/model 1/i)).toBeInTheDocument()
      fireEvent.click(screen.getByRole('button', { name: /remove model/i }))
      expect(screen.queryByText(/model 1/i)).not.toBeInTheDocument()
    })

    it('empty state message reappears once all models are removed', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      fireEvent.click(screen.getByRole('button', { name: /remove model/i }))
      expect(screen.getByText(/no data models defined/i)).toBeInTheDocument()
    })

    it('removing one model from two leaves one model card', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      const removeButtons = screen.getAllByRole('button', { name: /remove model/i })
      fireEvent.click(removeButtons[0])
      expect(screen.getAllByRole('button', { name: /remove model/i })).toHaveLength(1)
    })
  })

  describe('fields', () => {
    it('model card contains an Add Field button', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      expect(screen.getByRole('button', { name: /add field/i })).toBeInTheDocument()
    })

    it('clicking Add Field makes a field name input appear', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      fireEvent.click(screen.getByRole('button', { name: /add field/i }))
      expect(screen.getByPlaceholderText(/fieldName/i)).toBeInTheDocument()
    })

    it('field row contains a Type select defaulting to string', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      fireEvent.click(screen.getByRole('button', { name: /add field/i }))
      expect(screen.getByDisplayValue('string')).toBeInTheDocument()
    })

    it('field type select contains the expected primitive types', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      fireEvent.click(screen.getByRole('button', { name: /add field/i }))
      expect(screen.getByRole('option', { name: 'int' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'boolean' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'date' })).toBeInTheDocument()
    })

    it('field row contains a Required checkbox', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      fireEvent.click(screen.getByRole('button', { name: /add field/i }))
      expect(screen.getByText(/required|必填/i)).toBeInTheDocument()
      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes.length).toBeGreaterThan(0)
    })

    it('typing in the field name input is reflected in service state', () => {
      const { getService } = renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      fireEvent.click(screen.getByRole('button', { name: /add field/i }))
      fireEvent.change(screen.getByPlaceholderText(/fieldName/i), {
        target: { value: 'email' }
      })
      expect(getService().models[0].fields[0].name).toBe('email')
    })

    it('can delete a field by clicking its × button', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      fireEvent.click(screen.getByRole('button', { name: /add field/i }))
      expect(screen.getByPlaceholderText(/fieldName/i)).toBeInTheDocument()
      fireEvent.click(screen.getByTitle(/remove field|移除欄位/i))
      expect(screen.queryByPlaceholderText(/fieldName/i)).not.toBeInTheDocument()
    })

    it('removing a field restores "No fields defined" placeholder', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      fireEvent.click(screen.getByRole('button', { name: /add field/i }))
      fireEvent.click(screen.getByTitle(/remove field|移除欄位/i))
      expect(screen.getByText(/no fields defined/i)).toBeInTheDocument()
    })

    it('can add multiple fields to the same model', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add model/i }))
      fireEvent.click(screen.getByRole('button', { name: /add field/i }))
      fireEvent.click(screen.getByRole('button', { name: /add field/i }))
      expect(screen.getAllByPlaceholderText(/fieldName/i)).toHaveLength(2)
    })
  })
})
