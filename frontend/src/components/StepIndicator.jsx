import React from 'react'

export default function StepIndicator({ currentStep, totalSteps, labels }) {
  return (
    <div className="step-indicator">
      {Array.from({ length: totalSteps }, (_, i) => {
        const stepNum = i + 1
        const isCompleted = stepNum < currentStep
        const isActive = stepNum === currentStep

        return (
          <React.Fragment key={stepNum}>
            <div className={`step-item ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
              <div className="step-circle">
                {isCompleted ? (
                  <span className="step-check">&#10003;</span>
                ) : (
                  <span>{stepNum}</span>
                )}
              </div>
              <span className="step-label">{labels[i]}</span>
            </div>
            {stepNum < totalSteps && (
              <div className={`step-connector ${isCompleted ? 'completed' : ''}`} />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}
