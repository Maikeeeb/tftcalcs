import { FormEvent, forwardRef, useImperativeHandle } from 'react';
import { render, screen, waitFor, waitForElementToBeRemoved, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material';
import { vi } from 'vitest';
import type { ConfigData, SolverResponse } from '../types';

vi.mock('@rjsf/validator-ajv8', () => ({ __esModule: true, default: {} }));
vi.mock('@rjsf/mui', () => {
  const MockForm = forwardRef<any, any>((props, ref) => {
    useImperativeHandle(ref, () => ({ submit: () => props.onSubmit?.({ formData: props.formData }) }));
    const handleSubmit = (event: FormEvent) => {
      event.preventDefault();
      props.onSubmit?.({ formData: props.formData });
    };
    return (
      <form onSubmit={handleSubmit}>
        {props.children}
      </form>
    );
  });
  return { __esModule: true, default: MockForm };
});

import App from '../App';

const schema = {
  type: 'object',
  properties: {
    required_champions: {
      type: 'object',
      additionalProperties: { type: 'integer' },
    },
    required_traits_min: {
      type: 'object',
      additionalProperties: { type: 'integer' },
    },
    emblem_start_counts: {
      type: 'object',
      additionalProperties: { type: 'integer' },
    },
  mode: {
    type: 'string',
    enum: ['bronze', 'standard', 'ryze'],
  },
    must_have_itemized_tank: { type: 'boolean' },
  },
};

const defaultConfig: ConfigData = {
  required_champions: {
    TFT16_Tristana: 1,
    TFT16_Lulu: 0,
  },
  required_traits_min: {
    Invoker: 1,
  },
  emblem_start_counts: {
    Invoker: 0,
  },
  mode: 'standard',
  must_have_itemized_tank: false,
};

const solverResponse: SolverResponse = {
  context: { mode: 'standard' },
  meta: {
    enabled: true,
    weights: { w_win: 1, w_avg: 1, w_freq: 1 },
    unit_stats: {
      TFT16_Tristana: { win: 0.4, freq: 0.6, avg: 2.3, items: ['Sunfire Cape'] },
      TFT16_Lulu: { win: 0.3, freq: 0.3, avg: 3.1, items: ['Jeweled Gauntlet'] },
    },
    trait_stats_enabled: true,
  },
  solution: {
    team: ['TFT16_Tristana', 'TFT16_Lulu', 'TFT16_Teemo'],
    emblems: { Invoker: 1 },
    team_power: 10,
    bronze_count: 1,
    trait_counts: { Invoker: 2 },
    bronze_traits: ['Invoker'],
    active_traits: ['Invoker'],
    upgraded_traits: [],
    used_traits: ['Invoker'],
    trait_metatft: {
      Invoker: { required: 2, tier: 'S', avg: 4.2, win: 5.1, freq: 6.3 },
    },
  },
  units: {
    TFT16_Tristana: { traits: ['Invoker'], cost: 1, metatft: { win: 0.4, freq: 0.6, avg: 2.3, items: ['Sunfire Cape'] } },
    TFT16_Lulu: { traits: ['Invoker'], cost: 2, metatft: { win: 0.3, freq: 0.3, avg: 3.1, items: ['Jeweled Gauntlet'] } },
    TFT16_Teemo: { traits: ['Invoker'], cost: 1, metatft: { win: 0.2, freq: 0.2, avg: 4.2 } },
  },
  requirements: {
    champions: {
      TFT16_Tristana: { rule: 1, present: true, status: 'ok', satisfied: true },
      TFT16_Lulu: { rule: 0, present: true, status: 'ok', satisfied: true },
    },
    traits: { Invoker: { minimum: 1, actual: 2, satisfied: true } },
    all_satisfied: true,
  },
};

const createFetchMock = () => {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === 'string' ? input : input.toString();
    if (url.endsWith('/schema')) {
      return new Response(JSON.stringify(schema), { status: 200 });
    }
    if (url.endsWith('/config')) {
      return new Response(JSON.stringify(defaultConfig), { status: 200 });
    }
    if (url.endsWith('/run')) {
      return new Response(JSON.stringify(solverResponse), { status: 200 });
    }
    throw new Error(`Unexpected request to ${url}`);
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
};

const renderApp = () => {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <ThemeProvider theme={createTheme({ palette: { mode: 'light' } })}>
        <App mode="light" onToggleColorMode={() => {}} />
      </ThemeProvider>
    </QueryClientProvider>,
  );
};

describe('App', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('loads configuration, hydrates the form, and renders results after running the solver', async () => {
    const fetchMock = createFetchMock();
    renderApp();

    expect(await screen.findByText('Loading…')).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));
    expect(screen.getByText('Standard mode UI')).toBeInTheDocument();
    expect(screen.getByLabelText('Must have itemized tank')).not.toBeChecked();

    await userEvent.click(screen.getByLabelText('Must have itemized tank'));
    await userEvent.click(screen.getByRole('button', { name: 'Run solver' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/run', expect.anything()));
    const runCall = fetchMock.mock.calls.find(([url]) => typeof url === 'string' && url.endsWith('/run'));
    const body = JSON.parse((runCall?.[1] as RequestInit).body as string);
    expect(body.must_have_itemized_tank).toBe(true);

    expect(await screen.findByText('Copy code')).toBeInTheDocument();
    const rosterTitle = screen.getAllByText('TFT16_Tristana')[0];
    const roster = rosterTitle.closest('div');
    expect(roster).toBeTruthy();
    expect(within(roster as HTMLElement).getByText(/Cost: 1/)).toBeInTheDocument();
  });

  it('switches between bronze, standard, and ryze modes', async () => {
    const fetchMock = createFetchMock();
    renderApp();
    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));

    const bronzeButton = screen.getByRole('button', { name: 'Bronze for Life' });
    const standardButton = screen.getByRole('button', { name: 'Standard' });
    const ryzeButton = screen.getByRole('button', { name: 'Ryze (region traits)' });

    await userEvent.click(bronzeButton);
    await waitFor(() => expect(screen.getByText('Bronze for Life UI')).toBeInTheDocument());

    await userEvent.click(ryzeButton);
    await waitFor(() => {
      expect(screen.getByText('Ryze mode UI')).toBeInTheDocument();
      expect(screen.getByText(/Ryze mode counts only origin traits/)).toBeInTheDocument();
    });

    await userEvent.click(standardButton);
    await waitFor(() => expect(screen.getByText('Standard mode UI')).toBeInTheDocument());
  });

  it('switches between comp and itemization tabs', async () => {
    const fetchMock = createFetchMock();
    renderApp();
    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));

    const itemizationTab = screen.getByRole('tab', { name: 'Itemization' });
    await userEvent.click(itemizationTab);

    await waitFor(() => {
      expect(screen.getByText('Itemization finder')).toBeInTheDocument();
    });

    const compTab = screen.getByRole('tab', { name: 'Comp finder' });
    await userEvent.click(compTab);

    await waitFor(() => {
      expect(screen.getByText('Standard mode UI')).toBeInTheDocument();
    });
  });

  it('displays error when API fails to load', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('Network error'));
    vi.stubGlobal('fetch', fetchMock);
    renderApp();

    // Wait for error to appear (React Query will retry, so we need to wait)
    await waitFor(
      () => {
        expect(screen.getByText(/Failed to load schema or default config/)).toBeInTheDocument();
      },
      { timeout: 10000 },
    );
  }, 15000);

  it('displays solver error with debug log', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input.toString();
      if (url.endsWith('/schema')) {
        return new Response(JSON.stringify(schema), { status: 200 });
      }
      if (url.endsWith('/config')) {
        return new Response(JSON.stringify(defaultConfig), { status: 200 });
      }
      if (url.endsWith('/run')) {
        return new Response(
          JSON.stringify({
            detail: {
              error: 'Solver failed',
              debug_log: ['Debug line 1', 'Debug line 2'],
            },
          }),
          { status: 500 },
        );
      }
      throw new Error(`Unexpected request to ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);
    renderApp();

    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));
    await userEvent.click(screen.getByRole('button', { name: 'Run solver' }));

    await waitFor(() => {
      expect(screen.getByText(/Solver failed/)).toBeInTheDocument();
      expect(screen.getByText('Solver debug log')).toBeInTheDocument();
    });
  });

  it('toggles dark mode', async () => {
    const fetchMock = createFetchMock();
    const onToggleColorMode = vi.fn();
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <ThemeProvider theme={createTheme({ palette: { mode: 'dark' } })}>
          <App mode="dark" onToggleColorMode={onToggleColorMode} />
        </ThemeProvider>
      </QueryClientProvider>,
    );

    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));

    const modeSwitch = screen.getByLabelText('Dark mode');
    await userEvent.click(modeSwitch);

    expect(onToggleColorMode).toHaveBeenCalled();
  });

  it('shows loading state during solver run', async () => {
    let resolveRun: (value: any) => void;
    const runPromise = new Promise<SolverResponse>((resolve) => {
      resolveRun = resolve;
    });

    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input.toString();
      if (url.endsWith('/schema')) {
        return new Response(JSON.stringify(schema), { status: 200 });
      }
      if (url.endsWith('/config')) {
        return new Response(JSON.stringify(defaultConfig), { status: 200 });
      }
      if (url.endsWith('/run')) {
        await runPromise;
        return new Response(JSON.stringify(solverResponse), { status: 200 });
      }
      throw new Error(`Unexpected request to ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);
    renderApp();

    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));
    const runButton = screen.getByRole('button', { name: 'Run solver' });
    await userEvent.click(runButton);

    expect(screen.getByText('Running…')).toBeInTheDocument();
    expect(runButton).toBeDisabled();

    resolveRun!(solverResponse);
    await waitFor(() => {
      expect(screen.queryByText('Running…')).not.toBeInTheDocument();
    });
  });
});
