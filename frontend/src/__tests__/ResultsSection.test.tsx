import { describe, it, expect } from 'vitest';
import { render, screen } from './test-utils';
import ResultsSection from '../components/ResultsSection';
import { mockSolverResponse } from './test-data';

describe('ResultsSection', () => {
  it('renders all result components', () => {
    render(<ResultsSection response={mockSolverResponse} mustHaveItemizedTank={false} />);
    expect(screen.getByText('Team')).toBeInTheDocument();
    const traitsTexts = screen.getAllByText('Traits');
    expect(traitsTexts.length).toBeGreaterThan(0);
    expect(screen.getByText('Requirements')).toBeInTheDocument();
    expect(screen.getByText('Meta')).toBeInTheDocument();
  });

  it('passes mustHaveItemizedTank prop to TeamRoster', () => {
    render(<ResultsSection response={mockSolverResponse} mustHaveItemizedTank={true} />);
    expect(screen.getByText('Team')).toBeInTheDocument();
  });

  it('renders debug log when present', () => {
    const response = {
      ...mockSolverResponse,
      debug_log: ['Debug line 1', 'Debug line 2'],
    };
    render(<ResultsSection response={response} mustHaveItemizedTank={false} />);
    expect(screen.getByText('Solver debug log')).toBeInTheDocument();
  });

  it('does not render debug log when absent', () => {
    const response = {
      ...mockSolverResponse,
      debug_log: undefined,
    };
    render(<ResultsSection response={response} mustHaveItemizedTank={false} />);
    expect(screen.queryByText('Solver debug log')).not.toBeInTheDocument();
  });
});
