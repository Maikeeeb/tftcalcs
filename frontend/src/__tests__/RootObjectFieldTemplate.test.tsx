import { describe, it, expect, vi } from 'vitest';
import { render, screen } from './test-utils';
import userEvent from '@testing-library/user-event';
import RootObjectFieldTemplate from '../components/RootObjectFieldTemplate';
import type { ObjectFieldTemplateProps } from '@rjsf/utils';

const createMockProps = (overrides?: Partial<ObjectFieldTemplateProps>): ObjectFieldTemplateProps => {
  const DefaultTemplate = vi.fn(() => <div>Default Template</div>);
  const DescriptionTemplate = vi.fn((props: any) => <div>{props.description}</div>);

  return {
    title: 'Test Form',
    description: 'Test description',
    properties: [
      {
        name: 'regular_field',
        content: <div>Regular Field</div>,
      },
      {
        name: 'json_path',
        content: <div>JSON Path Field</div>,
      },
      {
        name: 'beam_width',
        content: <div>Beam Width Field</div>,
      },
    ],
    required: false,
    disabled: false,
    readonly: false,
    uiSchema: {},
    schema: { type: 'object' },
    formData: {},
    idSchema: { $id: 'root' } as any,
    onAddClick: vi.fn(),
    registry: {
      templates: {
        ObjectFieldTemplate: DefaultTemplate,
        DescriptionFieldTemplate: DescriptionTemplate,
      },
    } as any,
    ...overrides,
  };
};

describe('RootObjectFieldTemplate', () => {
  it('renders title when provided', () => {
    const props = createMockProps();
    render(<RootObjectFieldTemplate {...props} />);
    expect(screen.getByText('Test Form')).toBeInTheDocument();
  });

  it('renders description when provided', () => {
    const props = createMockProps();
    render(<RootObjectFieldTemplate {...props} />);
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('separates regular and advanced fields', () => {
    const props = createMockProps();
    render(<RootObjectFieldTemplate {...props} />);
    expect(screen.getByText('Regular Field')).toBeInTheDocument();
    expect(screen.getByText('Advanced solver settings')).toBeInTheDocument();
  });

  it('groups advanced fields in accordion', async () => {
    const props = createMockProps();
    render(<RootObjectFieldTemplate {...props} />);

    const accordion = screen.getByText('Advanced solver settings');
    expect(accordion).toBeInTheDocument();

    await userEvent.click(accordion);
    expect(screen.getByText('JSON Path Field')).toBeInTheDocument();
    expect(screen.getByText('Beam Width Field')).toBeInTheDocument();
  });

  it('uses default template for non-root fields', () => {
    const props = createMockProps({
      idSchema: { $id: 'nested' } as any,
    });
    render(<RootObjectFieldTemplate {...props} />);
    expect(screen.getByText('Default Template')).toBeInTheDocument();
  });

  it('handles missing registry gracefully', () => {
    const props = createMockProps({
      registry: undefined as any,
    });
    const { container } = render(<RootObjectFieldTemplate {...props} />);
    expect(container.firstChild).toBeNull();
  });

  it('handles no advanced fields', () => {
    const props = createMockProps({
      properties: [
        {
          name: 'regular_field',
          content: <div>Regular Field</div>,
        },
      ],
    });
    render(<RootObjectFieldTemplate {...props} />);
    expect(screen.getByText('Regular Field')).toBeInTheDocument();
    expect(screen.queryByText('Advanced solver settings')).not.toBeInTheDocument();
  });

  it('identifies all advanced field names', () => {
    const advancedFields = [
      'json_path',
      'set_id',
      'metatft_txt_path',
      'beam_width',
      'blacklist_traits_by_name',
    ];

    advancedFields.forEach((fieldName) => {
      const props = createMockProps({
        properties: [
          {
            name: fieldName,
            content: <div>{fieldName} Content</div>,
          },
        ],
      });
      const { unmount } = render(<RootObjectFieldTemplate {...props} />);
      expect(screen.getByText('Advanced solver settings')).toBeInTheDocument();
      unmount();
    });
  });
});
