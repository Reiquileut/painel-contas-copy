import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { StatusBadge } from './StatusBadge'

describe('StatusBadge', () => {
  it.each([
    ['pending', 'Pendente'],
    ['approved', 'Aprovada'],
    ['in_copy', 'Em Copy'],
    ['expired', 'Expirada'],
    ['suspended', 'Suspensa'],
  ] as const)('renders %s label', (status, label) => {
    render(<StatusBadge status={status} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })
})
