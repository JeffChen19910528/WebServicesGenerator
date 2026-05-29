import { render, screen, fireEvent, within } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import MethodBuilder from '../components/MethodBuilder'

const baseService = {
  service_name: 'TestService',
  service_type: 'REST',
  namespace: 'http://example.com/service',
  description: '',
  version: '1.0',
  methods: [],
  models: []
}

/**
 * Because MethodBuilder uses functional setService updates (prev => ...),
 * we wire up a real state simulation so that interactions that depend on
 * rendered method cards actually work.
 */
function renderWithState(initialService) {
  let currentService = { ...initialService, methods: [...initialService.methods] }
  const setService = vi.fn(updater => {
    currentService = typeof updater === 'function' ? updater(currentService) : updater
    rerender(<MethodBuilder service={currentService} setService={setService} />)
  })
  const { rerender } = render(
    <MethodBuilder service={currentService} setService={setService} />
  )
  return { setService, getService: () => currentService }
}

describe('MethodBuilder', () => {
  describe('empty state', () => {
    it('renders the Add Method button', () => {
      render(<MethodBuilder service={baseService} setService={vi.fn()} />)
      expect(screen.getByRole('button', { name: /add method/i })).toBeInTheDocument()
    })

    it('shows empty state message when no methods exist', () => {
      render(<MethodBuilder service={baseService} setService={vi.fn()} />)
      expect(screen.getByText(/no methods defined yet/i)).toBeInTheDocument()
    })

    it('does not render any method cards when methods array is empty', () => {
      render(<MethodBuilder service={baseService} setService={vi.fn()} />)
      expect(screen.queryByText(/method 1/i)).not.toBeInTheDocument()
    })
  })

  describe('adding methods', () => {
    it('clicking Add Method causes a method card to appear', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      expect(screen.getByText(/method 1/i)).toBeInTheDocument()
    })

    it('method card contains a Method Name input after adding', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      expect(screen.getByPlaceholderText(/e\.g\. getUser/i)).toBeInTheDocument()
    })

    it('can fill in the method name input', () => {
      const { getService } = renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      const nameInput = screen.getByPlaceholderText(/e\.g\. getUser/i)
      fireEvent.change(nameInput, { target: { value: 'createUser' } })
      expect(getService().methods[0].name).toBe('createUser')
    })

    it('adding two methods shows Method 1 and Method 2 headings', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      expect(screen.getByText(/method 1/i)).toBeInTheDocument()
      expect(screen.getByText(/method 2/i)).toBeInTheDocument()
    })
  })

  describe('HTTP method selector visibility', () => {
    it('shows HTTP Method selector when service_type is REST', () => {
      renderWithState({ ...baseService, service_type: 'REST' })
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      // The label "HTTP Method" should appear
      expect(screen.getByText('HTTP Method')).toBeInTheDocument()
    })

    it('shows HTTP Method selector when service_type is BOTH', () => {
      renderWithState({ ...baseService, service_type: 'BOTH' })
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      expect(screen.getByText('HTTP Method')).toBeInTheDocument()
    })

    it('hides HTTP Method selector when service_type is SOAP', () => {
      renderWithState({ ...baseService, service_type: 'SOAP' })
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      expect(screen.queryByText('HTTP Method')).not.toBeInTheDocument()
    })

    it('HTTP method select contains standard HTTP verbs for REST services', () => {
      renderWithState({ ...baseService, service_type: 'REST' })
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      const httpSelect = screen.getByDisplayValue('GET')
      expect(within(httpSelect.closest('div')).getByText('GET')).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'POST' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'PUT' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'DELETE' })).toBeInTheDocument()
    })
  })

  describe('removing methods', () => {
    it('clicking Remove Method removes the method card', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      expect(screen.getByText(/method 1/i)).toBeInTheDocument()
      fireEvent.click(screen.getByRole('button', { name: /remove method/i }))
      expect(screen.queryByText(/method 1/i)).not.toBeInTheDocument()
    })

    it('empty state message reappears after all methods are removed', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      fireEvent.click(screen.getByRole('button', { name: /remove method/i }))
      expect(screen.getByText(/no methods defined yet/i)).toBeInTheDocument()
    })
  })

  describe('parameters', () => {
    it('method card contains an Add Parameter button', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      expect(screen.getByRole('button', { name: /add parameter/i })).toBeInTheDocument()
    })

    it('shows "No parameters defined" when a method has no parameters', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      expect(screen.getByText(/no parameters defined/i)).toBeInTheDocument()
    })

    it('clicking Add Parameter makes parameter name input appear', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      fireEvent.click(screen.getByRole('button', { name: /add parameter/i }))
      expect(screen.getByPlaceholderText(/paramName/i)).toBeInTheDocument()
    })

    it('parameter row contains a Type select defaulting to string', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      fireEvent.click(screen.getByRole('button', { name: /add parameter/i }))
      expect(screen.getByDisplayValue('string')).toBeInTheDocument()
    })

    it('parameter row shows Location select for REST services', () => {
      renderWithState({ ...baseService, service_type: 'REST' })
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      fireEvent.click(screen.getByRole('button', { name: /add parameter/i }))
      expect(screen.getByText('Location')).toBeInTheDocument()
    })

    it('parameter row hides Location select for SOAP services', () => {
      renderWithState({ ...baseService, service_type: 'SOAP' })
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      fireEvent.click(screen.getByRole('button', { name: /add parameter/i }))
      expect(screen.queryByText('Location')).not.toBeInTheDocument()
    })

    it('can remove a parameter by clicking its × button', () => {
      renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      fireEvent.click(screen.getByRole('button', { name: /add parameter/i }))
      expect(screen.getByPlaceholderText(/paramName/i)).toBeInTheDocument()
      // The remove parameter button has title "Remove parameter"
      fireEvent.click(screen.getByTitle(/remove parameter/i))
      expect(screen.queryByPlaceholderText(/paramName/i)).not.toBeInTheDocument()
    })

    it('updating parameter name is reflected in service state', () => {
      const { getService } = renderWithState(baseService)
      fireEvent.click(screen.getByRole('button', { name: /add method/i }))
      fireEvent.click(screen.getByRole('button', { name: /add parameter/i }))
      fireEvent.change(screen.getByPlaceholderText(/paramName/i), {
        target: { value: 'userId' }
      })
      expect(getService().methods[0].parameters[0].name).toBe('userId')
    })
  })
})
