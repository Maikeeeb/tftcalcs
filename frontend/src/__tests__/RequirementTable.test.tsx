import { describe, it, expect } from 'vitest';
import { render, screen } from './test-utils';
import RequirementTable from '../components/RequirementTable';
import { mockSolverResponse } from './test-data';

describe('RequirementTable', () => {
  it('renders champion rules table', () => {
    render(<RequirementTable requirements={mockSolverResponse.requirements} />);
    expect(screen.getByText('Champion rules')).toBeInTheDocument();
    expect(screen.getByText('TFT16_Tristana')).toBeInTheDocument();
    expect(screen.getByText('TFT16_Lulu')).toBeInTheDocument();
  });

  it('renders trait minimums table', () => {
    render(<RequirementTable requirements={mockSolverResponse.requirements} />);
    expect(screen.getByText('Trait minimums')).toBeInTheDocument();
    expect(screen.getByText('Invoker')).toBeInTheDocument();
  });

  it('shows satisfied status correctly', () => {
    render(<RequirementTable requirements={mockSolverResponse.requirements} />);
    const satisfiedCells = screen.getAllByText('Satisfied');
    expect(satisfiedCells.length).toBeGreaterThan(0);
  });

  it('shows missing status for unsatisfied requirements', () => {
    const requirements = {
      ...mockSolverResponse.requirements,
      champions: {
        TFT16_Tristana: {
          rule: 1,
          present: false,
          status: 'missing',
          satisfied: false,
        },
      },
    };
    render(<RequirementTable requirements={requirements} />);
    expect(screen.getByText('Missing')).toBeInTheDocument();
  });

  it('highlights unsatisfied rows', () => {
    const requirements = {
      ...mockSolverResponse.requirements,
      champions: {
        TFT16_Tristana: {
          rule: 1,
          present: false,
          status: 'missing',
          satisfied: false,
        },
      },
    };
    render(<RequirementTable requirements={requirements} />);
    const rows = screen.getAllByRole('row');
    const unsatisfiedRow = rows.find((row) => {
      const ariaSelected = row.getAttribute('aria-selected');
      return ariaSelected === 'true' || row.classList.toString().includes('Mui-selected');
    });
    expect(unsatisfiedRow).toBeTruthy();
  });

  it('handles empty requirements', () => {
    const emptyRequirements = {
      champions: {},
      traits: {},
      all_satisfied: true,
    };
    render(<RequirementTable requirements={emptyRequirements} />);
    expect(screen.getByText('Champion rules')).toBeInTheDocument();
    expect(screen.getByText('Trait minimums')).toBeInTheDocument();
  });

  it('displays rule status', () => {
    render(<RequirementTable requirements={mockSolverResponse.requirements} />);
    const okTexts = screen.getAllByText('ok');
    expect(okTexts.length).toBeGreaterThan(0);
  });

  it('displays present/not present status', () => {
    render(<RequirementTable requirements={mockSolverResponse.requirements} />);
    expect(screen.getAllByText('Yes').length).toBeGreaterThan(0);
  });

  it('displays trait minimum and actual values', () => {
    render(<RequirementTable requirements={mockSolverResponse.requirements} />);
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });
});
