import { describe, it, expect } from 'vitest';
import { render, screen } from './test-utils';
import ItemizationResults from '../components/ItemizationResults';
import { mockItemizationResponse } from './test-data';

describe('ItemizationResults', () => {
  it('renders candidate cards', () => {
    render(
      <ItemizationResults
        result={mockItemizationResponse.result}
        nameMap={mockItemizationResponse.result.items.names_by_api}
      />,
    );
    expect(screen.getByText('TFT16_Tristana')).toBeInTheDocument();
  });

  it('displays candidate score information', () => {
    render(
      <ItemizationResults
        result={mockItemizationResponse.result}
        nameMap={mockItemizationResponse.result.items.names_by_api}
      />,
    );
    expect(screen.getByText(/Full items: 2/)).toBeInTheDocument();
    expect(screen.getByText(/completed 1, reforged 0, craftable 1/)).toBeInTheDocument();
  });

  it('renders ideal items', () => {
    render(
      <ItemizationResults
        result={mockItemizationResponse.result}
        nameMap={mockItemizationResponse.result.items.names_by_api}
      />,
    );
    expect(screen.getByText('Ideal items')).toBeInTheDocument();
    const infinityEdgeChips = screen.getAllByText('Infinity Edge');
    expect(infinityEdgeChips.length).toBeGreaterThan(0);
    const rapidFireChips = screen.getAllByText('Rapid Firecannon');
    expect(rapidFireChips.length).toBeGreaterThan(0);
  });

  it('renders suggested slams', () => {
    render(
      <ItemizationResults
        result={mockItemizationResponse.result}
        nameMap={mockItemizationResponse.result.items.names_by_api}
      />,
    );
    expect(screen.getByText('Suggested slams')).toBeInTheDocument();
    const rapidFireChips = screen.getAllByText('Rapid Firecannon');
    expect(rapidFireChips.length).toBeGreaterThan(0);
  });

  it('shows no slams message when empty', () => {
    const result = {
      ...mockItemizationResponse.result,
      solution: {
        ranked_candidates: [
          {
            ...mockItemizationResponse.result.solution.ranked_candidates[0],
            suggested_slams: [],
          },
        ],
      },
    };
    render(
      <ItemizationResults result={result} nameMap={mockItemizationResponse.result.items.names_by_api} />,
    );
    expect(screen.getByText('No immediate slams.')).toBeInTheDocument();
  });

  it('renders missing components', () => {
    render(
      <ItemizationResults
        result={mockItemizationResponse.result}
        nameMap={mockItemizationResponse.result.items.names_by_api}
      />,
    );
    expect(screen.getByText('Missing components')).toBeInTheDocument();
    expect(screen.getByText('B.F. Sword')).toBeInTheDocument();
  });

  it('shows no missing components message when empty', () => {
    const result = {
      ...mockItemizationResponse.result,
      solution: {
        ranked_candidates: [
          {
            ...mockItemizationResponse.result.solution.ranked_candidates[0],
            missing_components: [],
          },
        ],
      },
    };
    render(
      <ItemizationResults result={result} nameMap={mockItemizationResponse.result.items.names_by_api} />,
    );
    expect(screen.getByText('No missing components for preferred items.')).toBeInTheDocument();
  });

  it('renders trait shells', () => {
    render(
      <ItemizationResults
        result={mockItemizationResponse.result}
        nameMap={mockItemizationResponse.result.items.names_by_api}
      />,
    );
    expect(screen.getByText('Trait shells')).toBeInTheDocument();
    const invokerChips = screen.getAllByText('Invoker');
    expect(invokerChips.length).toBeGreaterThan(0);
  });

  it('renders team trait matches', () => {
    render(
      <ItemizationResults
        result={mockItemizationResponse.result}
        nameMap={mockItemizationResponse.result.items.names_by_api}
      />,
    );
    expect(screen.getByText('Team trait matches')).toBeInTheDocument();
    expect(screen.getByText('Yordle')).toBeInTheDocument();
  });

  it('shows no team trait matches message when empty', () => {
    const result = {
      ...mockItemizationResponse.result,
      solution: {
        ranked_candidates: [
          {
            ...mockItemizationResponse.result.solution.ranked_candidates[0],
            team_trait_matches: [],
          },
        ],
      },
    };
    render(
      <ItemizationResults result={result} nameMap={mockItemizationResponse.result.items.names_by_api} />,
    );
    expect(screen.getByText('No overlaps with current team traits.')).toBeInTheDocument();
  });

  it('renders needed trait matches', () => {
    render(
      <ItemizationResults
        result={mockItemizationResponse.result}
        nameMap={mockItemizationResponse.result.items.names_by_api}
      />,
    );
    expect(screen.getByText('Needed trait matches')).toBeInTheDocument();
    const invokerChips = screen.getAllByText('Invoker');
    expect(invokerChips.length).toBeGreaterThan(0);
  });

  it('shows no needed trait matches message when empty', () => {
    const result = {
      ...mockItemizationResponse.result,
      solution: {
        ranked_candidates: [
          {
            ...mockItemizationResponse.result.solution.ranked_candidates[0],
            needed_trait_matches: [],
          },
        ],
      },
    };
    render(
      <ItemizationResults result={result} nameMap={mockItemizationResponse.result.items.names_by_api} />,
    );
    expect(screen.getByText('No overlaps with needed traits.')).toBeInTheDocument();
  });

  it('handles multiple candidates', () => {
    const result = {
      ...mockItemizationResponse.result,
      solution: {
        ranked_candidates: [
          mockItemizationResponse.result.solution.ranked_candidates[0],
          {
            ...mockItemizationResponse.result.solution.ranked_candidates[0],
            champion: 'TFT16_Lulu',
          },
        ],
      },
    };
    render(
      <ItemizationResults result={result} nameMap={mockItemizationResponse.result.items.names_by_api} />,
    );
    expect(screen.getByText('TFT16_Tristana')).toBeInTheDocument();
    expect(screen.getByText('TFT16_Lulu')).toBeInTheDocument();
  });

  it('uses nameMap for item names', () => {
    const nameMap = {
      Infinity_Edge: 'Custom Infinity Edge',
      Rapid_Firecannon: 'Custom RFC',
    };
    render(
      <ItemizationResults
        result={mockItemizationResponse.result}
        nameMap={{ ...mockItemizationResponse.result.items.names_by_api, ...nameMap }}
      />,
    );
    const customInfinityChips = screen.getAllByText('Custom Infinity Edge');
    expect(customInfinityChips.length).toBeGreaterThan(0);
    const customRFCChips = screen.getAllByText('Custom RFC');
    expect(customRFCChips.length).toBeGreaterThan(0);
  });

  it('falls back to API name when nameMap missing', () => {
    render(
      <ItemizationResults
        result={mockItemizationResponse.result}
        nameMap={{}}
      />,
    );
    expect(screen.getByText('Infinity_Edge')).toBeInTheDocument();
  });
});
