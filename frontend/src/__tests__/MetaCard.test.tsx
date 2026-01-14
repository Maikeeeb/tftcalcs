import { describe, it, expect } from 'vitest';
import { render, screen } from './test-utils';
import MetaCard from '../components/MetaCard';
import { mockSolverResponse, mockStandardResponse } from './test-data';

describe('MetaCard', () => {
  it('renders mode information', () => {
    render(<MetaCard response={mockSolverResponse} />);
    expect(screen.getByText(/Mode: bronze/i)).toBeInTheDocument();
  });

  it('renders MetaTFT weights status', () => {
    render(<MetaCard response={mockSolverResponse} />);
    expect(screen.getByText(/MetaTFT weights enabled/i)).toBeInTheDocument();
  });

  it('shows disabled MetaTFT weights', () => {
    const response = {
      ...mockSolverResponse,
      meta: { ...mockSolverResponse.meta, enabled: false },
    };
    render(<MetaCard response={response} />);
    expect(screen.getByText(/MetaTFT weights disabled/i)).toBeInTheDocument();
  });

  it('renders weight values', () => {
    render(<MetaCard response={mockSolverResponse} />);
    expect(screen.getByText(/w_win: 1, w_avg: 1, w_freq: 1/)).toBeInTheDocument();
  });

  it('renders trait stats enabled status when present', () => {
    render(<MetaCard response={mockSolverResponse} />);
    expect(screen.getByText(/Trait preferences from MetaTFT enabled/i)).toBeInTheDocument();
  });

  it('does not render trait stats when undefined', () => {
    const response = {
      ...mockSolverResponse,
      meta: { ...mockSolverResponse.meta, trait_stats_enabled: undefined },
    };
    render(<MetaCard response={response} />);
    expect(screen.queryByText(/Trait preferences/)).not.toBeInTheDocument();
  });

  it('handles standard mode', () => {
    render(<MetaCard response={mockStandardResponse} />);
    expect(screen.getByText(/Mode: standard/i)).toBeInTheDocument();
  });
});
