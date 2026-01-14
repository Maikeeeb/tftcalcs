import { describe, it, expect } from 'vitest';
import { render, screen } from './test-utils';
import RequirementsCard from '../components/RequirementsCard';
import { mockSolverResponse } from './test-data';

describe('RequirementsCard', () => {
  it('renders success alert when all requirements satisfied', () => {
    render(<RequirementsCard response={mockSolverResponse} />);
    expect(screen.getByText('All requirements satisfied')).toBeInTheDocument();
    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
    expect(alert.className).toContain('MuiAlert-standardSuccess');
  });

  it('renders warning alert when requirements not satisfied', () => {
    const response = {
      ...mockSolverResponse,
      requirements: {
        ...mockSolverResponse.requirements,
        all_satisfied: false,
      },
    };
    render(<RequirementsCard response={response} />);
    expect(screen.getByText('Some requirements are not met')).toBeInTheDocument();
    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
    expect(alert.className).toContain('MuiAlert-standardWarning');
  });

  it('renders requirement table', () => {
    render(<RequirementsCard response={mockSolverResponse} />);
    expect(screen.getByText('Champion rules')).toBeInTheDocument();
    expect(screen.getByText('Trait minimums')).toBeInTheDocument();
  });
});
