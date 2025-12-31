import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material';
import { vi } from 'vitest';
import TeamRoster from '../components/TeamRoster';
import type { SolverResponse } from '../types';

const response: SolverResponse = {
  context: { mode: 'bronze' },
  meta: {
    enabled: false,
    weights: { w_win: 1, w_avg: 1, w_freq: 1 },
  },
  solution: {
    team: ['TFT16_Tristana', 'TFT16_Lulu'],
    emblems: {},
    team_power: 6,
    bronze_count: 0,
    trait_counts: { Yordle: 2 },
    bronze_traits: [],
    active_traits: ['Yordle'],
    upgraded_traits: [],
    used_traits: ['Yordle'],
  },
  units: {
    TFT16_Tristana: { traits: ['Yordle'], cost: 1, metatft: { items: ['Sunfire Cape', 'Warmogs Armor'], avg: 2 } },
    TFT16_Lulu: { traits: ['Yordle'], cost: 2, metatft: { items: ['Jeweled Gauntlet'], avg: 3 } },
  },
  requirements: {
    champions: {
      TFT16_Tristana: { rule: 1, present: true, status: 'ok', satisfied: true },
      TFT16_Lulu: { rule: 0, present: true, status: 'ok', satisfied: true },
    },
    traits: { Yordle: { minimum: 1, actual: 2, satisfied: true } },
    all_satisfied: true,
  },
};

describe('TeamRoster', () => {
  it('copies the team planner code and shows feedback', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, writable: true });

    render(
      <ThemeProvider theme={createTheme()}>
        <TeamRoster response={response} mustHaveItemizedTank={true} />
      </ThemeProvider>,
    );

    expect(screen.getByText('TFT16_Tristana')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Copy code' }));

    await waitFor(() => expect(writeText).toHaveBeenCalled());
    expect(writeText.mock.calls[0][0]).toMatch(/^02/);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Copied!' })).toBeInTheDocument());
  });
});
