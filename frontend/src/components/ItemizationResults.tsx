import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  Stack,
  Tooltip,
  Typography,
  LinearProgress,
} from '@mui/material';
import { CheckCircle, Cancel, Warning } from '@mui/icons-material';

import { ItemizationCandidate, ItemizationResult } from '../types';

type ItemizationResultsProps = {
  result: ItemizationResult;
  nameMap: Record<string, string>;
};

const renderItemList = (items: string[], nameMap: Record<string, string>) =>
  items.map((item) => <Chip key={item} label={nameMap[item] ?? item} size="small" />);

const CandidateCard = ({ candidate, nameMap }: { candidate: ItemizationCandidate; nameMap: Record<string, string> }) => {
  const totalScore = candidate.score.full_items;
  const maxScore = 3; // Assuming 3 items is the maximum
  const completionPercentage = (totalScore / maxScore) * 100;

  return (
    <Card variant="outlined" sx={{ '&:hover': { boxShadow: 2 } }}>
      <CardHeader
        title={
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {candidate.champion}
            </Typography>
            {totalScore === maxScore ? (
              <Tooltip title="Complete build">
                <CheckCircle color="success" fontSize="small" />
              </Tooltip>
            ) : totalScore === 0 ? (
              <Tooltip title="No items available">
                <Cancel color="disabled" fontSize="small" />
              </Tooltip>
            ) : (
              <Tooltip title={`${totalScore}/${maxScore} items available`}>
                <Warning color="warning" fontSize="small" />
              </Tooltip>
            )}
          </Stack>
        }
        subheader={
          <Stack spacing={0.5} sx={{ mt: 1 }}>
            <LinearProgress
              variant="determinate"
              value={completionPercentage}
              color={totalScore === maxScore ? 'success' : totalScore > 0 ? 'warning' : 'error'}
              sx={{ height: 6, borderRadius: 1 }}
            />
            <Typography variant="caption" color="text.secondary">
              Build progress: {totalScore}/{maxScore} items (
              {totalScore === maxScore ? 'Complete' : `${totalScore - candidate.score.reforged_items} existing, ${candidate.score.reforged_items} reforged, ${candidate.score.craftable_items} craftable`}
              )
            </Typography>
          </Stack>
        }
      />
      <CardContent>
        <Stack spacing={2.5}>
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 1 }}>
              Ideal Items
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {candidate.ideal_items.length ? (
                renderItemList(candidate.ideal_items, nameMap)
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No ideal items defined
                </Typography>
              )}
            </Stack>
          </Box>

          {candidate.suggested_slams.length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 1 }}>
                Suggested Slams
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {renderItemList(candidate.suggested_slams, nameMap)}
              </Stack>
            </Box>
          )}

          {candidate.missing_components.length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 1, color: 'warning.main' }}>
                Missing Components
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {renderItemList(candidate.missing_components, nameMap)}
              </Stack>
            </Box>
          )}

          {(candidate.trait_shells.length > 0 ||
            candidate.team_trait_matches.length > 0 ||
            candidate.needed_trait_matches.length > 0) && (
            <>
              <Divider />
              <Stack spacing={2}>
                {candidate.trait_shells.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 1 }}>
                      Trait Shells
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      {candidate.trait_shells.map((trait) => (
                        <Chip key={trait} label={trait} size="small" variant="outlined" />
                      ))}
                    </Stack>
                  </Box>
                )}

                {candidate.team_trait_matches.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 1 }}>
                      Team Trait Matches
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      {candidate.team_trait_matches.map((trait) => (
                        <Chip key={trait} label={trait} size="small" color="success" variant="outlined" />
                      ))}
                    </Stack>
                  </Box>
                )}

                {candidate.needed_trait_matches.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 1 }}>
                      Needed Trait Matches
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      {candidate.needed_trait_matches.map((trait) => (
                        <Chip key={trait} label={trait} size="small" color="info" variant="outlined" />
                      ))}
                    </Stack>
                  </Box>
                )}
              </Stack>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};

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
