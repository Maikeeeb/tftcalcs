import { Card, CardContent, CardHeader, Stack, Typography } from '@mui/material';

import { SolverResponse } from '../types';

function MetaCard({ response }: { response: SolverResponse }) {
  const { meta } = response;
  return (
    <Card>
      <CardHeader title="Meta" />
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="body1">Mode: {(response.context.mode as string) ?? 'bronze'}</Typography>
          <Typography variant="body1">MetaTFT weights {meta.enabled ? 'enabled' : 'disabled'}</Typography>
          <Typography variant="body2" color="text.secondary">
            w_win: {meta.weights.w_win}, w_avg: {meta.weights.w_avg}, w_freq: {meta.weights.w_freq}
          </Typography>
          {meta.trait_stats_enabled !== undefined ? (
            <Typography variant="body2" color="text.secondary">
              Trait preferences from MetaTFT {meta.trait_stats_enabled ? 'enabled' : 'disabled'}
            </Typography>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

export default MetaCard;
