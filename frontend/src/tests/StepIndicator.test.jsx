import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import StepIndicator from '../components/StepIndicator'

const defaultLabels = ['Basic Info', 'Methods', 'Data Models', 'Frameworks', 'Download']

describe('StepIndicator', () => {
  describe('renders the correct number of steps', () => {
    it('renders 5 step items when totalSteps is 5', () => {
      render(
        <StepIndicator currentStep={1} totalSteps={5} labels={defaultLabels} />
      )
      // Each step has a label rendered as .step-label — one per step
      const labels = screen.getAllByText(/basic info|methods|data models|frameworks|download/i)
      expect(labels).toHaveLength(5)
    })

    it('renders 4 connector lines between 5 steps', () => {
      const { container } = render(
        <StepIndicator currentStep={1} totalSteps={5} labels={defaultLabels} />
      )
      const connectors = container.querySelectorAll('.step-connector')
      expect(connectors).toHaveLength(4)
    })
  })

  describe('step labels', () => {
    it('shows "Basic Info" label', () => {
      render(<StepIndicator currentStep={1} totalSteps={5} labels={defaultLabels} />)
      expect(screen.getByText('Basic Info')).toBeInTheDocument()
    })

    it('shows "Methods" label', () => {
      render(<StepIndicator currentStep={1} totalSteps={5} labels={defaultLabels} />)
      expect(screen.getByText('Methods')).toBeInTheDocument()
    })

    it('shows "Data Models" label', () => {
      render(<StepIndicator currentStep={1} totalSteps={5} labels={defaultLabels} />)
      expect(screen.getByText('Data Models')).toBeInTheDocument()
    })

    it('shows "Frameworks" label', () => {
      render(<StepIndicator currentStep={1} totalSteps={5} labels={defaultLabels} />)
      expect(screen.getByText('Frameworks')).toBeInTheDocument()
    })

    it('shows "Download" label', () => {
      render(<StepIndicator currentStep={1} totalSteps={5} labels={defaultLabels} />)
      expect(screen.getByText('Download')).toBeInTheDocument()
    })
  })

  describe('active step styling', () => {
    it('step 1 item has the "active" class when currentStep is 1', () => {
      const { container } = render(
        <StepIndicator currentStep={1} totalSteps={5} labels={defaultLabels} />
      )
      const stepItems = container.querySelectorAll('.step-item')
      expect(stepItems[0]).toHaveClass('active')
    })

    it('step 3 item has the "active" class when currentStep is 3', () => {
      const { container } = render(
        <StepIndicator currentStep={3} totalSteps={5} labels={defaultLabels} />
      )
      const stepItems = container.querySelectorAll('.step-item')
      expect(stepItems[2]).toHaveClass('active')
    })

    it('step 5 item has the "active" class when currentStep is 5', () => {
      const { container } = render(
        <StepIndicator currentStep={5} totalSteps={5} labels={defaultLabels} />
      )
      const stepItems = container.querySelectorAll('.step-item')
      expect(stepItems[4]).toHaveClass('active')
    })

    it('only one step has the "active" class at a time', () => {
      const { container } = render(
        <StepIndicator currentStep={3} totalSteps={5} labels={defaultLabels} />
      )
      const activeItems = container.querySelectorAll('.step-item.active')
      expect(activeItems).toHaveLength(1)
    })
  })

  describe('completed step styling', () => {
    it('steps before the current step have the "completed" class', () => {
      const { container } = render(
        <StepIndicator currentStep={4} totalSteps={5} labels={defaultLabels} />
      )
      const stepItems = container.querySelectorAll('.step-item')
      // Steps 1, 2, 3 should be completed (indices 0, 1, 2)
      expect(stepItems[0]).toHaveClass('completed')
      expect(stepItems[1]).toHaveClass('completed')
      expect(stepItems[2]).toHaveClass('completed')
    })

    it('the current step and future steps do not have the "completed" class', () => {
      const { container } = render(
        <StepIndicator currentStep={3} totalSteps={5} labels={defaultLabels} />
      )
      const stepItems = container.querySelectorAll('.step-item')
      // Step 3 (index 2) is active, steps 4 & 5 (indices 3, 4) are neither active nor completed
      expect(stepItems[2]).not.toHaveClass('completed')
      expect(stepItems[3]).not.toHaveClass('completed')
      expect(stepItems[4]).not.toHaveClass('completed')
    })

    it('no steps are completed when currentStep is 1', () => {
      const { container } = render(
        <StepIndicator currentStep={1} totalSteps={5} labels={defaultLabels} />
      )
      const completedItems = container.querySelectorAll('.step-item.completed')
      expect(completedItems).toHaveLength(0)
    })

    it('connectors before the active step have the "completed" class', () => {
      const { container } = render(
        <StepIndicator currentStep={3} totalSteps={5} labels={defaultLabels} />
      )
      const connectors = container.querySelectorAll('.step-connector')
      // Connector 0 (between step 1 and 2) and connector 1 (between step 2 and 3) should be completed
      expect(connectors[0]).toHaveClass('completed')
      expect(connectors[1]).toHaveClass('completed')
      // Connector 2 (between step 3 and 4) should not be completed
      expect(connectors[2]).not.toHaveClass('completed')
    })
  })

  describe('completed step check mark', () => {
    it('completed steps display a checkmark instead of a step number', () => {
      render(<StepIndicator currentStep={3} totalSteps={5} labels={defaultLabels} />)
      // The component renders ✓ (Unicode U+2713) for completed steps
      const checkmarks = screen.getAllByText('✓')
      // Steps 1 and 2 are completed when currentStep is 3
      expect(checkmarks).toHaveLength(2)
    })

    it('active and future steps display their step number, not a checkmark', () => {
      render(<StepIndicator currentStep={2} totalSteps={5} labels={defaultLabels} />)
      // Step 1 is completed, so steps 2-5 should show numbers
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByText('4')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
    })
  })
})
