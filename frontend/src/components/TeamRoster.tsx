import { useEffect, useMemo, useState } from 'react';
import { CheckCircle, ContentCopy } from '@mui/icons-material';
import {
  Alert,
  Avatar,
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  Grid,
  Stack,
  Tooltip,
  Typography,
  Button,
} from '@mui/material';

import { buildTeamPlannerCode, getTeamPlannerSlotCount } from '../teamPlanner';
import { SolverResponse } from '../types';
import {
  championAvatarImgProps,
  countTankItems,
  getChampionImage,
  getEmblemImage,
  getItemImage,
  getTraitImage,
  isTankItemBuild,
} from '../utils/assets';

function TeamRoster({ response, mustHaveItemizedTank }: { response: SolverResponse; mustHaveItemizedTank: boolean }) {
  const { solution, units, meta } = response;
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle');
  const teamPlannerCode = useMemo(() => buildTeamPlannerCode(solution.team), [solution.team]);
  const traitCounts = solution.trait_counts ?? {};
  const traitMetatft = solution.trait_metatft ?? {};
  const mode = (response.context.mode as 'bronze' | 'standard' | 'ryze' | undefined) ?? 'bronze';
  const traitLabel = mode === 'ryze' ? 'Region traits' : 'Bronze traits';

  useEffect(() => {
    setCopyStatus('idle');
  }, [teamPlannerCode.code]);

  const handleCopyCode = async () => {
    if (!teamPlannerCode.code) return;
    try {
      await navigator.clipboard.writeText(teamPlannerCode.code);
      setCopyStatus('copied');
      setTimeout(() => setCopyStatus('idle'), 2000);
    } catch (err) {
      console.error('Failed to copy team planner code', err);
      setCopyStatus('error');
    }
  };

  const { topUnits, topUnitItems } = useMemo(() => {
    const weightedScores = solution.team.map((unit, index) => {
      const stats = units[unit]?.metatft ?? (meta.unit_stats?.[unit] as SolverResponse['units'][string]['metatft']);
      const winScore = (stats?.win ?? 0) * (meta.weights.w_win ?? 1);
      const freqScore = (stats?.freq ?? 0) * (meta.weights.w_freq ?? 1);
      const avgScore = (stats?.avg ?? 0) * (meta.weights.w_avg ?? 1);
      const score = winScore + freqScore - avgScore;

      return { unit, score, items: stats?.items ?? [], index };
    });

    weightedScores.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.index - b.index;
    });
    const limit = Math.min(3, weightedScores.length);

    const tankCandidates = weightedScores.filter((entry) => isTankItemBuild(entry.items));
    const fallbackTankCandidates = weightedScores
      .map((entry) => ({ ...entry, tankCount: countTankItems(entry.items) }))
      .filter((entry) => entry.tankCount > 0)
      .sort((a, b) => {
        if (b.tankCount !== a.tankCount) return b.tankCount - a.tankCount;
        return b.score - a.score;
      });

    const chosenTank = mustHaveItemizedTank
      ? tankCandidates[0] ?? fallbackTankCandidates[0] ?? null
      : null;

    const selected: typeof weightedScores = [];
    if (chosenTank) {
      selected.push(chosenTank);
    }

    for (const entry of weightedScores) {
      if (selected.some((sel) => sel.unit === entry.unit)) continue;
      if (mustHaveItemizedTank && chosenTank && isTankItemBuild(entry.items)) continue;
      selected.push(entry);
      if (selected.length >= limit) break;
    }

    if (selected.length < limit) {
      for (const entry of weightedScores) {
        if (selected.some((sel) => sel.unit === entry.unit)) continue;
        selected.push(entry);
        if (selected.length >= limit) break;
      }
    }

    return {
      topUnits: new Set(selected.map((entry) => entry.unit)),
      topUnitItems: new Map(selected.map((entry) => [entry.unit, entry.items])),
    };
  }, [
    meta.unit_stats,
    meta.weights.w_avg,
    meta.weights.w_freq,
    meta.weights.w_win,
    mustHaveItemizedTank,
    solution.team,
    units,
  ]);

  const missingItemImages = new Set<string>();

  const rosterCards = solution.team.map((unit) => {
    const info = units[unit];
    const showItems = topUnits.has(unit) ? topUnitItems.get(unit) ?? [] : [];
    showItems.forEach((item) => {
      if (!getItemImage(item)) {
        missingItemImages.add(item);
      }
    });
    const metatftStats = info?.metatft ?? (meta.unit_stats?.[unit] as SolverResponse['units'][string]['metatft']);
    return (
      <Grid item xs={12} sm={6} md={4} key={unit}>
        <Card variant="outlined">
          <CardHeader
            avatar={
              getChampionImage(unit) ? (
                <Avatar
                  src={getChampionImage(unit)}
                  alt={unit}
                  sx={{ width: 40, height: 40 }}
                  imgProps={championAvatarImgProps}
                />
              ) : undefined
            }
            title={unit}
            subheader={`Cost: ${info?.cost ?? 'N/A'}`}
            action={
              showItems.length ? (
                <Stack direction="row" spacing={0.5} alignItems="center" flexWrap="wrap">
                  {showItems.map((item) => (
                    <Tooltip title={item} key={`${unit}-${item}`}>
                      <Avatar
                        variant="rounded"
                        src={getItemImage(item)}
                        alt={item}
                        sx={{ width: 32, height: 32 }}
                      >
                        {getItemImage(item) ? null : item.slice(0, 2)}
                      </Avatar>
                    </Tooltip>
                  ))}
                </Stack>
              ) : null
            }
          />
          <CardContent>
            <Stack spacing={1}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Traits
                </Typography>
                <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                  {info?.traits
                    ?.filter((trait) => (traitCounts[trait] ?? 0) > 0)
                    .map((trait) => {
                      const count = traitCounts[trait] ?? 0;
                      const metaStats = traitMetatft[trait];
                      const metaParts: string[] = [];

                      if (metaStats?.tier) metaParts.push(`Tier ${metaStats.tier}`);
                      if (metaStats?.avg !== undefined) metaParts.push(`Avg ${metaStats.avg.toFixed(2)}`);
                      if (metaStats?.win !== undefined) metaParts.push(`Win ${metaStats.win.toFixed(2)}`);
                      if (metaStats?.freq !== undefined) metaParts.push(`Freq ${metaStats.freq.toFixed(2)}`);

                      const labelBase = `${count} ${trait}`;
                      const label = metaParts.length ? `${labelBase} (${metaParts.join(' • ')})` : labelBase;

                      return (
                        <Chip
                          key={trait}
                          label={label}
                          variant="outlined"
                          avatar={
                            getTraitImage(trait) ? (
                              <Avatar src={getTraitImage(trait)} alt={trait} sx={{ width: 24, height: 24 }} />
                            ) : undefined
                          }
                        />
                      );
                    })}
                </Stack>
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary">
                  MetaTFT stats
                </Typography>
                {metatftStats ? (
                  <Stack direction="row" spacing={1}>
                    {metatftStats.avg !== undefined ? (
                      <Chip label={`Avg: ${metatftStats.avg.toFixed(2)}`} size="small" />
                    ) : null}
                    {metatftStats.win !== undefined ? (
                      <Chip label={`Win: ${metatftStats.win.toFixed(2)}`} size="small" />
                    ) : null}
                    {metatftStats.freq !== undefined ? (
                      <Chip label={`Freq: ${metatftStats.freq.toFixed(2)}`} size="small" />
                    ) : null}
                  </Stack>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No MetaTFT stats
                  </Typography>
                )}
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Grid>
    );
  });

  const missingItemsList = Array.from(missingItemImages);

  return (
      <Card>
        <CardHeader
          title="Team"
          subheader={`Team power: ${solution.team_power.toFixed(2)} • ${traitLabel}: ${solution.bronze_count}`}
        />
      <CardContent>
        <Stack spacing={2}>
          <Box>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
              <Tooltip
                placement="top"
                title={
                  teamPlannerCode.missing.length
                    ? `Missing mapping for: ${teamPlannerCode.missing.join(', ')}`
                    : teamPlannerCode.trimmed
                        ? `Limited to first ${getTeamPlannerSlotCount()} unique units.`
                        : 'Copy team code to clipboard'
                }
              >
                <span>
                  <Button
                    variant="outlined"
                    startIcon={copyStatus === 'copied' ? <CheckCircle /> : <ContentCopy />}
                    color={copyStatus === 'error' ? 'error' : 'primary'}
                    onClick={handleCopyCode}
                    disabled={!teamPlannerCode.code}
                  >
                    {copyStatus === 'copied' ? 'Copied!' : 'Copy code'}
                  </Button>
                </span>
              </Tooltip>
            </Stack>
            {teamPlannerCode.missing.length ? (
              <Alert severity="warning" sx={{ mt: 1 }}>
                Missing team planner mapping for: {teamPlannerCode.missing.join(', ')}.
              </Alert>
            ) : null}
            {teamPlannerCode.trimmed ? (
              <Alert severity="info" sx={{ mt: 1 }}>
                Only the first {getTeamPlannerSlotCount()} unique units are included in the code. Remove duplicates to
                include all champions.
              </Alert>
            ) : null}
            {copyStatus === 'error' ? (
              <Alert severity="error" sx={{ mt: 1 }}>
                Failed to copy the code. Please try again or copy it manually from the field.
              </Alert>
            ) : null}
          </Box>
          {missingItemsList.length ? (
            <Alert severity="warning" variant="outlined">
              Missing images for: {missingItemsList.join(', ')}. Please report this so we can add the art.
            </Alert>
          ) : null}
          <Grid container spacing={2}>
            {rosterCards}
          </Grid>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default TeamRoster;
