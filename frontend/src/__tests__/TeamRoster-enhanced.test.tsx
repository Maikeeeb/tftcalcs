import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from './test-utils';
import userEvent from '@testing-library/user-event';
import TeamRoster from '../components/TeamRoster';
import { mockSolverResponse } from './test-data';

describe('TeamRoster enhanced', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('displays team power and bronze count', () => {
    render(<TeamRoster response={mockSolverResponse} mustHaveItemizedTank={false} />);
    expect(screen.getByText(/Team power: 10/)).toBeInTheDocument();
    expect(screen.getByText(/Bronze traits: 1/)).toBeInTheDocument();
  });

  it('displays region traits label for ryze mode', () => {
    const ryzeResponse = {
      ...mockSolverResponse,
      context: { mode: 'ryze' },
    };
    render(<TeamRoster response={ryzeResponse} mustHaveItemizedTank={false} />);
    expect(screen.getByText(/Region traits: 1/)).toBeInTheDocument();
  });

  it('handles missing unit data gracefully', () => {
    const response = {
      ...mockSolverResponse,
      units: {
        TFT16_Tristana: mockSolverResponse.units.TFT16_Tristana,
      },
    };
    render(<TeamRoster response={response} mustHaveItemizedTank={false} />);
    expect(screen.getByText('TFT16_Tristana')).toBeInTheDocument();
  });

  it('shows missing items warning', () => {
    const response = {
      ...mockSolverResponse,
      units: {
        TFT16_Tristana: {
          ...mockSolverResponse.units.TFT16_Tristana,
          metatft: {
            ...mockSolverResponse.units.TFT16_Tristana.metatft!,
            items: ['Unknown_Item'],
          },
        },
      },
    };
    render(<TeamRoster response={response} mustHaveItemizedTank={false} />);
    expect(screen.getByText(/Missing images for:/)).toBeInTheDocument();
  });

  it('shows missing team planner mapping warning', () => {
    const response = {
      ...mockSolverResponse,
      solution: {
        ...mockSolverResponse.solution,
        team: ['Unknown_Unit'],
      },
      units: {
        Unknown_Unit: {
          traits: [],
          cost: 1,
        },
      },
    };
    render(<TeamRoster response={response} mustHaveItemizedTank={false} />);
    expect(screen.getByText(/Missing team planner mapping for:/)).toBeInTheDocument();
  });

  it('handles copy error', async () => {
    const writeText = vi.fn().mockRejectedValue(new Error('Clipboard error'));
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      writable: true,
    });

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(<TeamRoster response={mockSolverResponse} mustHaveItemizedTank={false} />);

    const copyButton = screen.getByRole('button', { name: 'Copy code' });
    await userEvent.click(copyButton);

    await waitFor(() => {
      expect(screen.getByText(/Failed to copy the code/)).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('selects tank when mustHaveItemizedTank is true', () => {
    const response = {
      ...mockSolverResponse,
      units: {
        TFT16_Tristana: {
          ...mockSolverResponse.units.TFT16_Tristana,
          metatft: {
            ...mockSolverResponse.units.TFT16_Tristana.metatft!,
            items: ['Sunfire Cape', 'Warmogs'],
          },
        },
        TFT16_Lulu: mockSolverResponse.units.TFT16_Lulu,
      },
    };
    render(<TeamRoster response={response} mustHaveItemizedTank={true} />);
    expect(screen.getByText('TFT16_Tristana')).toBeInTheDocument();
  });

  it('handles empty team', () => {
    const response = {
      ...mockSolverResponse,
      solution: {
        ...mockSolverResponse.solution,
        team: [],
      },
      units: {},
    };
    render(<TeamRoster response={response} mustHaveItemizedTank={false} />);
    expect(screen.getByText('Team')).toBeInTheDocument();
  });

  it('displays trait counts with MetaTFT stats', () => {
    render(<TeamRoster response={mockSolverResponse} mustHaveItemizedTank={false} />);
    const invokerTexts = screen.getAllByText(/Invoker/);
    expect(invokerTexts.length).toBeGreaterThan(0);
  });

  it('displays unit MetaTFT stats', () => {
    render(<TeamRoster response={mockSolverResponse} mustHaveItemizedTank={false} />);
    expect(screen.getByText(/Avg: 2.30/)).toBeInTheDocument();
    expect(screen.getByText(/Win: 0.40/)).toBeInTheDocument();
    expect(screen.getByText(/Freq: 0.60/)).toBeInTheDocument();
  });

  it('handles units without MetaTFT stats', () => {
    const response = {
      ...mockSolverResponse,
      units: {
        TFT16_Tristana: {
          traits: ['Invoker'],
          cost: 1,
          metatft: null,
        },
      },
    };
    render(<TeamRoster response={response} mustHaveItemizedTank={false} />);
    expect(screen.getByText('No MetaTFT stats')).toBeInTheDocument();
  });
});
