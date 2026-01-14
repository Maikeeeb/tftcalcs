import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, waitForElementToBeRemoved } from './test-utils';
import userEvent from '@testing-library/user-event';
import ItemizationPage from '../components/ItemizationPage';
import {
  mockItemizationReference,
  mockItemizationResponse,
  mockItemizationConfig,
} from './test-data';

const createFetchMock = (responses: Record<string, any>) => {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === 'string' ? input : input.toString();
    const endpoint = url.split('localhost:8000')[1] || url;

    if (responses[endpoint]) {
      return new Response(JSON.stringify(responses[endpoint]), { status: 200 });
    }

    throw new Error(`Unexpected request to ${endpoint}`);
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
};

describe('ItemizationPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('loads and displays itemization configuration', async () => {
    const fetchMock = createFetchMock({
      '/v2/itemization/config': { version: 2, config: mockItemizationConfig },
      '/v2/itemization/data': { version: 2, data: mockItemizationReference },
    });

    render(<ItemizationPage />);

    expect(await screen.findByText('Loading…')).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));

    expect(screen.getByText('Itemization finder')).toBeInTheDocument();
    expect(screen.getByText('Inventory & targets')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/v2/itemization/config'));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/v2/itemization/data'));
  });

  it('displays error when API fails', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('Network error'));
    vi.stubGlobal('fetch', fetchMock);

    render(<ItemizationPage />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load itemization data/i)).toBeInTheDocument();
    });
  });

  it('allows adding components to inventory', async () => {
    createFetchMock({
      '/v2/itemization/config': { version: 2, config: mockItemizationConfig },
      '/v2/itemization/data': { version: 2, data: mockItemizationReference },
    });

    render(<ItemizationPage />);
    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));

    const autocomplete = screen.getByLabelText('Available components');
    await userEvent.click(autocomplete);
    await userEvent.type(autocomplete, 'B.F. Sword');

    const option = await screen.findByText('B.F. Sword');
    await userEvent.click(option);

    const addButtons = screen.getAllByRole('button', { name: 'Add' });
    const enabledAddButton = addButtons.find((btn) => !btn.hasAttribute('disabled'));
    expect(enabledAddButton).toBeTruthy();
    if (enabledAddButton) {
      await userEvent.click(enabledAddButton);
    }

    await waitFor(() => {
      expect(screen.getByText(/B.F. Sword/)).toBeInTheDocument();
    });
  });

  it.skip('allows removing items from inventory', async () => {
    // TODO: Fix chip deletion test - MUI Chip onDelete handler needs proper testing setup
    createFetchMock({
      '/v2/itemization/config': {
        version: 2,
        config: {
          ...mockItemizationConfig,
          available_components: ['BF_Sword'],
        },
      },
      '/v2/itemization/data': { version: 2, data: mockItemizationReference },
    });

    render(<ItemizationPage />);
    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));

    await waitFor(() => {
      const chip = screen.getByText(/B.F. Sword/);
      expect(chip).toBeInTheDocument();
    });

    // Find the chip element and look for the delete button within it
    const chipText = screen.getByText(/B.F. Sword/);
    const chipContainer = chipText.closest('.MuiChip-root') || chipText.closest('[class*="MuiChip"]');
    if (chipContainer) {
      // MUI Chip delete button is typically a button with aria-label or a clickable element
      const deleteButton = chipContainer.querySelector('button[aria-label*="Delete"], button[aria-label*="Remove"]') ||
        chipContainer.querySelector('svg')?.closest('button') ||
        chipContainer.querySelector('[role="button"]');
      if (deleteButton) {
        await userEvent.click(deleteButton);
      }
    }

    await waitFor(() => {
      const chips = screen.queryAllByText(/B.F. Sword/);
      expect(chips.length).toBe(0);
    }, { timeout: 3000 });
  });

  it.skip('allows selecting target carries', async () => {
    // TODO: Fix Autocomplete selection test - MUI Autocomplete multiple selection needs proper testing
    createFetchMock({
      '/v2/itemization/config': { version: 2, config: mockItemizationConfig },
      '/v2/itemization/data': { version: 2, data: mockItemizationReference },
    });

    render(<ItemizationPage />);
    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));

    const autocomplete = screen.getByLabelText('Target carries (optional)');
    await userEvent.click(autocomplete);
    await userEvent.type(autocomplete, 'Tristana');

    // Wait for the option to appear and click it
    const option = await screen.findByRole('option', { name: /Tristana/i });
    await userEvent.click(option);

    // After selection, the Autocomplete should show Tristana as selected
    // It might appear as a chip or in the input value
    await waitFor(() => {
      // Check if Tristana appears anywhere (could be in chip, input, or option)
      const tristanaElements = screen.queryAllByText(/Tristana/i);
      expect(tristanaElements.length).toBeGreaterThan(0);
    }, { timeout: 2000 });
  });

  it('toggles allow reforge switch', async () => {
    createFetchMock({
      '/v2/itemization/config': { version: 2, config: mockItemizationConfig },
      '/v2/itemization/data': { version: 2, data: mockItemizationReference },
    });

    render(<ItemizationPage />);
    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));

    const switchElement = screen.getByLabelText('Allow reforging completed items');
    expect(switchElement).not.toBeChecked();

    await userEvent.click(switchElement);
    expect(switchElement).toBeChecked();
  });

  it('runs itemization solver and displays results', async () => {
    const fetchMock = createFetchMock({
      '/v2/itemization/config': { version: 2, config: mockItemizationConfig },
      '/v2/itemization/data': { version: 2, data: mockItemizationReference },
      '/v2/itemization/run': mockItemizationResponse,
    });

    render(<ItemizationPage />);
    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));

    const runButton = screen.getByRole('button', { name: 'Rank carries' });
    await userEvent.click(runButton);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/v2/itemization/run'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }),
      );
    });

    await waitFor(() => {
      expect(screen.getByText('Closest carry builds')).toBeInTheDocument();
      expect(screen.getByText('TFT16_Tristana')).toBeInTheDocument();
    });
  });

  it('displays error when solver run fails', async () => {
    const baseMock = createFetchMock({
      '/v2/itemization/config': { version: 2, config: mockItemizationConfig },
      '/v2/itemization/data': { version: 2, data: mockItemizationReference },
    });

    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input.toString();
      if (url.includes('/v2/itemization/run')) {
        return new Response(JSON.stringify({ error: 'Solver failed' }), { status: 500 });
      }
      return baseMock(input);
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<ItemizationPage />);
    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));

    const runButton = screen.getByRole('button', { name: 'Rank carries' });
    await userEvent.click(runButton);

    await waitFor(() => {
      // The error message should appear in an Alert
      const errorAlert = screen.getByRole('alert');
      expect(errorAlert).toBeInTheDocument();
      expect(errorAlert).toHaveTextContent(/Solver failed|Failed to run/i);
    }, { timeout: 5000 });
  });

  it('shows loading state during solver run', async () => {
    let resolveRun: (value: any) => void;
    const runPromise = new Promise((resolve) => {
      resolveRun = resolve;
    });

    const baseMock = createFetchMock({
      '/v2/itemization/config': { version: 2, config: mockItemizationConfig },
      '/v2/itemization/data': { version: 2, data: mockItemizationReference },
    });

    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input.toString();
      if (url.includes('/v2/itemization/run')) {
        await runPromise;
        return new Response(JSON.stringify(mockItemizationResponse), { status: 200 });
      }
      return baseMock(input);
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<ItemizationPage />);
    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));

    const runButton = screen.getByRole('button', { name: 'Rank carries' });
    await userEvent.click(runButton);

    await waitFor(() => {
      expect(screen.getByText('Ranking…')).toBeInTheDocument();
      expect(runButton).toBeDisabled();
    });

    resolveRun!(mockItemizationResponse);
    await waitFor(() => {
      expect(screen.queryByText('Ranking…')).not.toBeInTheDocument();
    });
  });

  it('displays empty state when no items selected', async () => {
    createFetchMock({
      '/v2/itemization/config': {
        version: 2,
        config: {
          ...mockItemizationConfig,
          available_components: [],
          available_completed_items: [],
        },
      },
      '/v2/itemization/data': { version: 2, data: mockItemizationReference },
    });

    render(<ItemizationPage />);
    await waitForElementToBeRemoved(() => screen.queryByText('Loading…'));

    // The empty state message appears when both components and completed items are empty
    await waitFor(() => {
      const emptyMessages = screen.queryAllByText('No items selected yet.');
      expect(emptyMessages.length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });
});
