import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Container,
  Divider,
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
  Button,
} from '@mui/material';
import Form from '@rjsf/mui';
import validator from '@rjsf/validator-ajv8';
import { TemplatesType } from '@rjsf/utils';
import { useMutation, useQuery } from '@tanstack/react-query';

type ConfigData = Record<string, unknown>;

type SolverResponse = {
  context: Record<string, unknown>;
  meta: {
    enabled: boolean;
    weights: {
      w_win: number;
      w_avg: number;
      w_freq: number;
    };
    unit_stats?: Record<string, { avg?: number; win?: number; freq?: number }>;
  };
  solution: {
    team: string[];
    emblems: Record<string, number>;
    team_power: number;
    bronze_count: number;
    trait_counts: Record<string, number>;
    bronze_traits: string[];
    active_traits: string[];
    upgraded_traits: string[];
    used_traits: string[];
  };
  units: Record<
    string,
    {
      traits: string[];
      cost?: number;
      metatft?: { avg?: number; win?: number; freq?: number } | null;
    }
  >;
  requirements: {
    champions: Record<string, { rule: number; present: boolean; status: string; satisfied: boolean }>;
    traits: Record<string, { minimum: number; actual: number; satisfied: boolean }>;
    all_satisfied: boolean;
  };
};

const API_BASE = 'http://localhost:8000';

const fetchJson = async <T,>(path: string): Promise<T> => {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch ${path}: ${res.statusText}`);
  }
  return (await res.json()) as T;
};

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
          <Chip key={trait} label={trait} color={color} variant="outlined" />
        ))}
      </Stack>
    </Box>
  );
}

function RequirementTable({
  requirements,
}: {
  requirements: SolverResponse['requirements'];
}) {
  const championEntries = Object.entries(requirements.champions || {});
  const traitEntries = Object.entries(requirements.traits || {});

  return (
    <Stack spacing={2}>
      <Typography variant="subtitle1">Champion rules</Typography>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Champion</TableCell>
            <TableCell>Rule</TableCell>
            <TableCell>Present</TableCell>
            <TableCell>OK?</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {championEntries.map(([name, detail]) => (
            <TableRow key={name} selected={!detail.satisfied}>
              <TableCell>{name}</TableCell>
              <TableCell>{detail.status}</TableCell>
              <TableCell>{detail.present ? 'Yes' : 'No'}</TableCell>
              <TableCell>{detail.satisfied ? 'Satisfied' : 'Missing'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Typography variant="subtitle1">Trait minimums</Typography>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Trait</TableCell>
            <TableCell>Minimum</TableCell>
            <TableCell>Actual</TableCell>
            <TableCell>OK?</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {traitEntries.map(([name, detail]) => (
            <TableRow key={name} selected={!detail.satisfied}>
              <TableCell>{name}</TableCell>
              <TableCell>{detail.minimum}</TableCell>
              <TableCell>{detail.actual}</TableCell>
              <TableCell>{detail.satisfied ? 'Satisfied' : 'Missing'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Stack>
  );
}

function TeamRoster({
  response,
}: {
  response: SolverResponse;
}) {
  const { solution, units } = response;

  return (
    <Card>
      <CardHeader title="Team roster" subheader={`Team power: ${solution.team_power.toFixed(2)}`} />
      <CardContent>
        <Grid container spacing={2}>
          {solution.team.map((unit) => {
            const info = units[unit];
            return (
              <Grid item xs={12} sm={6} md={4} key={unit}>
                <Card variant="outlined">
                  <CardHeader title={unit} subheader={`Cost: ${info?.cost ?? 'N/A'}`} />
                  <CardContent>
                    <Stack spacing={1}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Traits
                        </Typography>
                        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                          {info?.traits?.map((trait) => (
                            <Chip key={trait} label={trait} size="small" />
                          ))}
                        </Stack>
                      </Box>
                      {info?.metatft ? (
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            MetaTFT
                          </Typography>
                          <Stack direction="row" spacing={1}>
                            {'avg' in info.metatft && info.metatft.avg !== undefined && (
                              <Chip label={`Avg: ${info.metatft.avg.toFixed(2)}`} size="small" />
                            )}
                            {'win' in info.metatft && info.metatft.win !== undefined && (
                              <Chip label={`Win: ${info.metatft.win.toFixed(2)}`} size="small" />
                            )}
                            {'freq' in info.metatft && info.metatft.freq !== undefined && (
                              <Chip label={`Freq: ${info.metatft.freq.toFixed(2)}`} size="small" />
                            )}
                          </Stack>
                        </Box>
                      ) : null}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      </CardContent>
    </Card>
  );
}

function TraitsSummary({ response }: { response: SolverResponse }) {
  const { solution } = response;
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
              {Object.entries(solution.trait_counts).map(([trait, count]) => (
                <Chip key={trait} label={`${trait}: ${count}`} variant="outlined" />
              ))}
            </Stack>
          </Box>
          {Object.keys(solution.emblems).length ? (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Emblems
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {Object.entries(solution.emblems).map(([trait, count]) => (
                  <Chip key={trait} label={`${trait}: ${count}`} color="secondary" variant="outlined" />
                ))}
              </Stack>
            </Box>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

function RequirementsCard({ response }: { response: SolverResponse }) {
  const { requirements } = response;

  return (
    <Card>
      <CardHeader title="Requirements" />
      <CardContent>
        <Stack spacing={2}>
          <Alert severity={requirements.all_satisfied ? 'success' : 'warning'}>
            {requirements.all_satisfied ? 'All requirements satisfied' : 'Some requirements are not met'}
          </Alert>
          <RequirementTable requirements={requirements} />
        </Stack>
      </CardContent>
    </Card>
  );
}

function MetaCard({ response }: { response: SolverResponse }) {
  const { meta } = response;
  return (
    <Card>
      <CardHeader title="Meta" />
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="body1">
            MetaTFT weights {meta.enabled ? 'enabled' : 'disabled'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            w_win: {meta.weights.w_win}, w_avg: {meta.weights.w_avg}, w_freq: {meta.weights.w_freq}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

function ResultsSection({ response }: { response: SolverResponse }) {
  return (
    <Stack spacing={3} mt={2} mb={4}>
      <TeamRoster response={response} />
      <TraitsSummary response={response} />
      <RequirementsCard response={response} />
      <MetaCard response={response} />
    </Stack>
  );
}

function Loader() {
  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <CircularProgress size={20} />
      <Typography>Loading…</Typography>
    </Stack>
  );
}

function App() {
  const [formData, setFormData] = useState<ConfigData | undefined>();

  const schemaQuery = useQuery({ queryKey: ['schema'], queryFn: () => fetchJson<Record<string, unknown>>('/schema') });
  const configQuery = useQuery({ queryKey: ['config'], queryFn: () => fetchJson<ConfigData>('/config') });

  useEffect(() => {
    if (configQuery.data) {
      setFormData(configQuery.data);
    }
  }, [configQuery.data]);

  const runMutation = useMutation({
    mutationFn: async (data: ConfigData) => {
      const res = await fetch(`${API_BASE}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || 'Failed to run solver');
      }
      return (await res.json()) as SolverResponse;
    },
  });

  const templates: TemplatesType = useMemo(
    () => ({
      ButtonTemplates: {
        SubmitButton: (props) => (
          <Box textAlign="right" mt={2}>
            <Button
              type="submit"
              variant="contained"
              disabled={props.disabled || runMutation.isPending}
              endIcon={runMutation.isPending ? <CircularProgress size={16} color="inherit" /> : undefined}
            >
              {runMutation.isPending ? 'Running…' : 'Run solver'}
            </Button>
          </Box>
        ),
      },
    }),
    [runMutation.isPending]
  );

  const isLoading = schemaQuery.isLoading || configQuery.isLoading;
  const hasError = schemaQuery.error || configQuery.error;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Bronze for Life UI
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Edit the solver configuration via JSON Schema, then run Bronze for Life to view the resulting team, traits, and requirements.
          </Typography>
        </Box>

        <Card>
          <CardHeader title="Solver configuration" />
          <CardContent>
            {isLoading && <Loader />}
            {hasError && (
              <Alert severity="error">Failed to load schema or default config. Please ensure the API is running.</Alert>
            )}
            {!isLoading && !hasError && schemaQuery.data && formData ? (
              <Form
                schema={schemaQuery.data}
                formData={formData}
                onChange={(event) => setFormData(event.formData)}
                onSubmit={(event) => runMutation.mutate(event.formData)}
                validator={validator}
                templates={templates}
                liveValidate
              >
                <></>
              </Form>
            ) : null}
            {runMutation.error ? (
              <Alert severity="error" sx={{ mt: 2 }}>
                {(runMutation.error as Error).message}
              </Alert>
            ) : null}
          </CardContent>
        </Card>

        {runMutation.data ? <ResultsSection response={runMutation.data} /> : null}
      </Stack>
    </Container>
  );
}

export default App;
