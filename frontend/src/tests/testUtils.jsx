import React from 'react'
import { render } from '@testing-library/react'
import { LanguageProvider } from '../i18n/LanguageContext.jsx'

export function renderWithLang(ui, options) {
  return render(ui, {
    wrapper: ({ children }) => <LanguageProvider>{children}</LanguageProvider>,
    ...options
  })
}
