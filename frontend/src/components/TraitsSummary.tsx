import { Avatar, Box, Card, CardContent, CardHeader, Chip, Divider, Grid, Stack, Typography } from '@mui/material';

import { SolverResponse } from '../types';
import { getEmblemImage, getTraitImage } from '../utils/assets';

function TraitsPanel({
  title,
  traits,
  color,
}: {
  title: string;
  traits: string[];
  color: 'default' | 'primary' | 'secondary' | 'success' | 'warning';
}) {
  if (!traits?.length) {
    return null;
  }

  return (
    <Box>
      <Typography variant="subtitle1" gutterBottom>
        {title}
      </Typography>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        {traits.map((trait) => (
          <Chip
            key={trait}
            label={trait}
            color={color}
            variant="outlined"
            avatar={
              getTraitImage(trait) ? (
                <Avatar src={getTraitImage(trait)} alt={trait} sx={{ width: 24, height: 24 }} />
              ) : undefined
            }
          />
        ))}
      </Stack>
    </Box>
  );
}

function TraitsSummary({ response }: { response: SolverResponse }) {
  const { solution } = response;
  const traitMetatft = solution.trait_metatft ?? {};
  const traitCountEntries = Object.entries(solution.trait_counts).filter(([, count]) => count > 0);
  const emblemEntries = Object.entries(solution.emblems).filter(([, count]) => count > 0);
  return (
    <Card>
      <CardHeader title="Traits" subheader="Bronze, active, upgraded, and counts" />
      <CardContent>
        <Stack spacing={3}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TraitsPanel title="Bronze traits" traits={solution.bronze_traits} color="warning" />
            </Grid>
            <Grid item xs={12} md={4}>
              <TraitsPanel title="Active traits" traits={solution.active_traits} color="success" />
            </Grid>
            <Grid item xs={12} md={4}>
              <TraitsPanel title="Upgraded traits" traits={solution.upgraded_traits} color="primary" />
            </Grid>
          </Grid>
          <Divider />
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Trait counts
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {traitCountEntries.map(([trait, count]) => {
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
            <Typography variant="subtitle1" gutterBottom>
              Emblems
            </Typography>
            {emblemEntries.length ? (
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {emblemEntries.map(([trait, count]) => (
                  <Chip
                    key={trait}
                    label={`${trait}: ${count}`}
                    color="secondary"
                    variant="outlined"
                    avatar={
                      getEmblemImage(trait) ? (
                        <Avatar src={getEmblemImage(trait)} alt={`${trait} emblem`} sx={{ width: 24, height: 24 }} />
                      ) : undefined
                    }
                  />
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                no emblems considered
              </Typography>
            )}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default TraitsSummary;
