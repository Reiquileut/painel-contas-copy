import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Loading } from './Loading'

describe('Loading', () => {
  it('renders spinner container', () => {
    const { container } = render(<Loading />)
    expect(container.querySelector('.animate-spin')).toBeTruthy()
    expect(container.firstElementChild).toHaveClass('flex')
  })
})
