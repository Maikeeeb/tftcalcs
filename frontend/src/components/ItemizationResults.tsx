import { Box, Card, CardContent, CardHeader, Chip, Divider, Stack, Typography } from '@mui/material';

import { ItemizationCandidate, ItemizationResult } from '../types';

type ItemizationResultsProps = {
  result: ItemizationResult;
  nameMap: Record<string, string>;
};

const renderItemList = (items: string[], nameMap: Record<string, string>) =>
  items.map((item) => <Chip key={item} label={nameMap[item] ?? item} size="small" />);

const CandidateCard = ({ candidate, nameMap }: { candidate: ItemizationCandidate; nameMap: Record<string, string> }) => (
  <Card variant="outlined">
    <CardHeader
      title={candidate.champion}
      subheader={`Full items: ${candidate.score.full_items} (completed ${candidate.score.completed_items}, reforged ${candidate.score.reforged_items}, craftable ${candidate.score.craftable_items})`}
    />
    <CardContent>
      <Stack spacing={2}>
        <Box>
          <Typography variant="subtitle2">Ideal items</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {renderItemList(candidate.ideal_items, nameMap)}
          </Stack>
        </Box>
        <Box>
          <Typography variant="subtitle2">Suggested slams</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {candidate.suggested_slams.length ? (
              renderItemList(candidate.suggested_slams, nameMap)
            ) : (
              <Typography variant="body2" color="text.secondary">
                No immediate slams.
              </Typography>
            )}
          </Stack>
        </Box>
        <Box>
          <Typography variant="subtitle2">Missing components</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {candidate.missing_components.length ? (
              renderItemList(candidate.missing_components, nameMap)
            ) : (
              <Typography variant="body2" color="text.secondary">
                No missing components for preferred items.
              </Typography>
            )}
          </Stack>
        </Box>
        <Divider />
        <Box>
          <Typography variant="subtitle2">Trait shells</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {candidate.trait_shells.map((trait) => (
              <Chip key={trait} label={trait} size="small" variant="outlined" />
            ))}
          </Stack>
        </Box>
        <Box>
          <Typography variant="subtitle2">Team trait matches</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {candidate.team_trait_matches.length ? (
              candidate.team_trait_matches.map((trait) => (
                <Chip key={trait} label={trait} size="small" color="success" variant="outlined" />
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                No overlaps with current team traits.
              </Typography>
            )}
          </Stack>
        </Box>
        <Box>
          <Typography variant="subtitle2">Needed trait matches</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {candidate.needed_trait_matches.length ? (
              candidate.needed_trait_matches.map((trait) => (
                <Chip key={trait} label={trait} size="small" color="info" variant="outlined" />
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                No overlaps with needed traits.
              </Typography>
            )}
          </Stack>
        </Box>
      </Stack>
    </CardContent>
  </Card>
);

const ItemizationResults = ({ result, nameMap }: ItemizationResultsProps) => {
  const candidates = result.solution.ranked_candidates;
  return (
    <Stack spacing={2}>
      {candidates.map((candidate) => (
        <CandidateCard key={candidate.champion} candidate={candidate} nameMap={nameMap} />
      ))}
    </Stack>
  );
};

export default ItemizationResults;
