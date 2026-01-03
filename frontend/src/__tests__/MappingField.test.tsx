import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material';
import { vi } from 'vitest';
import MappingField from '../components/MappingField';
import type { MappingFieldOptions } from '../types';
import type { FieldProps } from '@rjsf/utils';

type MappingProps = FieldProps<Record<string, number>>;

const createProps = (options: MappingFieldOptions = {}): MappingProps => ({
  formData: {
    TFT16_Tristana: 0,
    TFT16_Lulu: 1,
    TFT16_Teemo: -1,
  },
  idSchema: { $id: 'root' } as unknown as MappingProps['idSchema'],
  name: 'required_champions',
  onChange: vi.fn(),
  onBlur: vi.fn(),
  onFocus: vi.fn(),
  registry: {} as MappingProps['registry'],
  required: false,
  disabled: false,
  readonly: false,
  uiSchema: { 'ui:options': options },
  schema: { type: 'object' },
  errorSchema: {},
  formContext: {},
  autofocus: false,
  rawErrors: [],
});

describe('MappingField', () => {
  it('filters entries based on search and unlockable toggles', async () => {
    const props = createProps({ unlockableValues: ['TFT16_Lulu'], searchPlaceholder: 'Search champions…' });
    render(
      <ThemeProvider theme={createTheme()}>
        <MappingField {...props} />
      </ThemeProvider>,
    );

    expect(screen.getByPlaceholderText('Search champions…')).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText('Search'), 'Lulu');
    expect(screen.getByText('TFT16_Lulu')).toBeInTheDocument();
    expect(screen.queryByText('TFT16_Tristana')).not.toBeInTheDocument();

    await userEvent.clear(screen.getByLabelText('Search'));
    await userEvent.click(screen.getByLabelText('Unlockables only'));
    expect(screen.getByText('TFT16_Lulu')).toBeInTheDocument();
    expect(screen.queryByText('TFT16_Teemo')).not.toBeInTheDocument();
  });

  it('applies cost toggles to mass-update champion rules', async () => {
    const props = createProps({
      imageType: 'champion',
      championCosts: { TFT16_Tristana: 1, TFT16_Lulu: 2, TFT16_Teemo: 1 },
      unlockableValues: ['TFT16_Lulu'],
    });
    render(
      <ThemeProvider theme={createTheme()}>
        <MappingField {...props} />
      </ThemeProvider>,
    );

    const toggle = screen.getByRole('button', { name: /1-cost/i });
    await userEvent.click(toggle);

    expect(toggle).toHaveAttribute('aria-pressed', 'false');
    const onChangeMock = props.onChange as unknown as ReturnType<typeof vi.fn>;
    expect(onChangeMock).toHaveBeenCalled();
    const updated = onChangeMock.mock.calls.at(-1)?.[0] as Record<string, number>;
    expect(updated.TFT16_Tristana).toBe(-1);
    expect(updated.TFT16_Lulu).toBe(1);
    expect(updated.TFT16_Teemo).toBe(-1);
  });

  it('allows editing numeric fields directly', async () => {
    const props = createProps();
    render(
      <ThemeProvider theme={createTheme()}>
        <MappingField {...props} />
      </ThemeProvider>,
    );

    const valueInput = screen.getAllByLabelText('Value')[0];
    await userEvent.clear(valueInput);
    await userEvent.type(valueInput, '3');

    const onChangeMock = props.onChange as unknown as ReturnType<typeof vi.fn>;
    expect(onChangeMock).toHaveBeenCalled();
    const updated = onChangeMock.mock.calls.at(-1)?.[0] as Record<string, number>;
    expect(updated.TFT16_Tristana).toBe(3);
  });
});
