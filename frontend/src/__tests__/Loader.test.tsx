import { describe, it, expect } from 'vitest';
import { render, screen } from './test-utils';
import Loader from '../components/Loader';

describe('Loader', () => {
  it('renders loading text', () => {
    render(<Loader />);
    expect(screen.getByText('Loading…')).toBeInTheDocument();
  });

  it('renders circular progress', () => {
    render(<Loader />);
    const progress = screen.getByRole('progressbar');
    expect(progress).toBeInTheDocument();
  });
});
