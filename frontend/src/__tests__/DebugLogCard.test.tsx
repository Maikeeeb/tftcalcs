import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from './test-utils';
import userEvent from '@testing-library/user-event';
import DebugLogCard from '../components/DebugLogCard';

describe('DebugLogCard', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders nothing when lines are empty', () => {
    const { container } = render(<DebugLogCard lines={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when lines are undefined', () => {
    const { container } = render(<DebugLogCard />);
    expect(container.firstChild).toBeNull();
  });

  it('renders debug log lines', () => {
    const lines = ['Line 1', 'Line 2', 'Line 3'];
    render(<DebugLogCard lines={lines} />);
    expect(screen.getByText('Solver debug log')).toBeInTheDocument();
    // The log text is rendered as a single pre element with newlines
    const preElement = screen.getByText(/Line 1[\s\S]*Line 2[\s\S]*Line 3/);
    expect(preElement).toBeInTheDocument();
  });

  it('copies log to clipboard', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      writable: true,
    });

    const lines = ['Debug line 1', 'Debug line 2'];
    render(<DebugLogCard lines={lines} />);

    const copyButton = screen.getByRole('button', { name: /copy log/i });
    await userEvent.click(copyButton);

    await waitFor(() => expect(writeText).toHaveBeenCalled());
    expect(writeText).toHaveBeenCalledWith('Debug line 1\nDebug line 2');
    expect(screen.getByText('Copied')).toBeInTheDocument();
  });

  it('handles copy error gracefully', async () => {
    const writeText = vi.fn().mockRejectedValue(new Error('Clipboard error'));
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      writable: true,
    });

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const lines = ['Test line'];
    render(<DebugLogCard lines={lines} />);

    const copyButton = screen.getByRole('button', { name: /copy log/i });
    await userEvent.click(copyButton);

    await waitFor(() => expect(consoleSpy).toHaveBeenCalled());
    consoleSpy.mockRestore();
  });

  it('resets copied state after timeout', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      writable: true,
    });

    const lines = ['Test'];
    render(<DebugLogCard lines={lines} />);

    const copyButton = screen.getByRole('button', { name: /copy log/i });
    await userEvent.click(copyButton);

    await waitFor(() => {
      expect(screen.getByText('Copied')).toBeInTheDocument();
    });

    await waitFor(
      () => {
        expect(screen.queryByText('Copied')).not.toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });
});
