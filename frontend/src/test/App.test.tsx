import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    // Check that the NobelLM title is present
    expect(screen.getByText('NobelLM')).toBeInTheDocument()
  })
}) 