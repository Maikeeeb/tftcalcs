import { describe, it, expect } from 'vitest';
import { render, screen } from './test-utils';
import TraitsSummary from '../components/TraitsSummary';
import { mockSolverResponse, mockRyzeResponse } from './test-data';

describe('TraitsSummary', () => {
  it('renders bronze traits panel', () => {
    render(<TraitsSummary response={mockSolverResponse} />);
    expect(screen.getByText('Bronze traits')).toBeInTheDocument();
    const invokerChips = screen.getAllByText('Invoker');
    expect(invokerChips.length).toBeGreaterThan(0);
  });

  it('renders active traits panel', () => {
    render(<TraitsSummary response={mockSolverResponse} />);
    expect(screen.getByText('Active traits')).toBeInTheDocument();
  });

  it('renders upgraded traits panel', () => {
    const response = {
      ...mockSolverResponse,
      solution: {
        ...mockSolverResponse.solution,
        upgraded_traits: ['Invoker'],
      },
    };
    render(<TraitsSummary response={response} />);
    expect(screen.getByText('Upgraded traits')).toBeInTheDocument();
    const invokerChips = screen.getAllByText('Invoker');
    expect(invokerChips.length).toBeGreaterThan(0);
  });

  it('renders trait counts with MetaTFT stats', () => {
    render(<TraitsSummary response={mockSolverResponse} />);
    expect(screen.getByText('Trait counts')).toBeInTheDocument();
    expect(screen.getByText(/2 Invoker/)).toBeInTheDocument();
  });

  it('renders emblems section', () => {
    render(<TraitsSummary response={mockSolverResponse} />);
    expect(screen.getByText('Emblems')).toBeInTheDocument();
    expect(screen.getByText(/Invoker: 1/)).toBeInTheDocument();
  });

  it('shows no emblems message when empty', () => {
    const response = {
      ...mockSolverResponse,
      solution: {
        ...mockSolverResponse.solution,
        emblems: {},
      },
    };
    render(<TraitsSummary response={response} />);
    expect(screen.getByText(/no emblems considered/i)).toBeInTheDocument();
  });

  it('uses region traits label for ryze mode', () => {
    render(<TraitsSummary response={mockRyzeResponse} />);
    expect(screen.getByText('Region traits')).toBeInTheDocument();
    expect(screen.queryByText('Bronze traits')).not.toBeInTheDocument();
  });

  it('filters out zero-count traits', () => {
    const response = {
      ...mockSolverResponse,
      solution: {
        ...mockSolverResponse.solution,
        trait_counts: { Invoker: 2, Yordle: 0 },
      },
    };
    render(<TraitsSummary response={response} />);
    expect(screen.getByText(/2 Invoker/)).toBeInTheDocument();
    expect(screen.queryByText(/0 Yordle/)).not.toBeInTheDocument();
  });

  it('handles missing trait_metatft', () => {
    const response = {
      ...mockSolverResponse,
      solution: {
        ...mockSolverResponse.solution,
        trait_metatft: undefined,
      },
    };
    render(<TraitsSummary response={response} />);
    expect(screen.getByText(/2 Invoker/)).toBeInTheDocument();
  });

  it('does not render empty trait panels', () => {
    const response = {
      ...mockSolverResponse,
      solution: {
        ...mockSolverResponse.solution,
        bronze_traits: [],
        active_traits: [],
        upgraded_traits: [],
      },
    };
    render(<TraitsSummary response={response} />);
    expect(screen.queryByText('Bronze traits')).not.toBeInTheDocument();
    expect(screen.queryByText('Active traits')).not.toBeInTheDocument();
    expect(screen.queryByText('Upgraded traits')).not.toBeInTheDocument();
  });
});
