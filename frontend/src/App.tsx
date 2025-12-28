import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Avatar,
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
  MenuItem,
  TextField,
  FormControlLabel,
  Switch,
  PaletteMode,
} from '@mui/material';
import Form from '@rjsf/mui';
import validator from '@rjsf/validator-ajv8';
import { FieldProps } from '@rjsf/utils';
import type CoreForm from '@rjsf/core';
import type { FormProps } from '@rjsf/core';
import { useMutation, useQuery } from '@tanstack/react-query';

type ConfigData = Record<string, unknown>;

type AppProps = {
  mode: PaletteMode;
  onToggleColorMode: () => void;
};

const normalizeKey = (value: string) => value.toLowerCase().replace(/[^a-z0-9]/g, '');

const assetModules = import.meta.glob('../tft-images/*', {
  eager: true,
  query: '?url',
  import: 'default',
});

const championImages: Record<string, string> = {};
const traitImages: Record<string, string> = {};
const emblemImages: Record<string, string> = {};

const championAvatarImgProps = { style: { objectPosition: '70% 50%' } } as const;

const aliasIfMissing = (
  targetKey: string,
  sourceKeys: string[],
  imageMap: Record<string, string>,
) => {
  if (imageMap[targetKey]) return;
  for (const source of sourceKeys) {
    if (imageMap[source]) {
      imageMap[targetKey] = imageMap[source];
      return;
    }
  }
};

Object.entries(assetModules).forEach(([path, urlValue]) => {
  const filename = path.split('/').pop() ?? '';
  const url = urlValue as string;
  const normalizedFilename = normalizeKey(filename);

  const championMatch = filename.match(/TFT\d+_(.+?)_splash/);
  if (championMatch) {
    championImages[normalizeKey(championMatch[1])] = url;
    return;
  }

  const emblemMatch = filename.match(/TFT\d+_Item_(.+?)EmblemItem/);
  if (emblemMatch) {
    emblemImages[normalizeKey(emblemMatch[1])] = url;
    return;
  }

  const traitMatch = filename.match(/Trait_Icon_\d+_(.+?)\./);
  if (traitMatch) {
    traitImages[normalizeKey(traitMatch[1])] = url;
    return;
  }

  if (normalizedFilename.includes('arcanist')) {
    traitImages.arcanist = url;
  }
});

aliasIfMissing('arcanist', ['sorcerer'], emblemImages);
aliasIfMissing('arcanist', ['sorcerer'], traitImages);

const getChampionImage = (name: string) => {
  const normalized = normalizeKey(name);
  const apiNameMatch = normalized.match(/^tft\d+(.*)$/);
  const candidates = [normalized];

  if (apiNameMatch?.[1]) {
    candidates.push(apiNameMatch[1]);
  }

  for (const candidate of candidates) {
    if (championImages[candidate]) {
      return championImages[candidate];
    }
  }

  return undefined;
};
const getTraitImage = (name: string) => traitImages[normalizeKey(name)];
const getEmblemImage = (name: string) =>
  emblemImages[normalizeKey(name)] ?? traitImages[normalizeKey(name)];

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

type MappingFieldOptions = {
  enumOptions?: { value: number; label: string }[];
  min?: number;
  heading?: string;
  searchPlaceholder?: string;
  imageType?: 'trait' | 'emblem' | 'champion';
};

function MappingField(props: FieldProps<Record<string, number>>) {
  const options = (props.uiSchema?.['ui:options'] as MappingFieldOptions | undefined) ?? {};
  const entries = Object.entries(props.formData ?? {});
  const [search, setSearch] = useState('');
  const [showAll, setShowAll] = useState(false);

  const filteredEntries = entries.filter(([key]) =>
    key.toLowerCase().includes(search.toLowerCase().trim()),
  );

  const previewLimit = 20;
  const isSearching = search.trim().length > 0;
  const visibleEntries = isSearching || showAll
    ? filteredEntries
    : filteredEntries.slice(0, previewLimit);

  const getAvatarSrc = (key: string) => {
    switch (options.imageType) {
      case 'champion':
        return getChampionImage(key);
      case 'emblem':
        return getEmblemImage(key);
      case 'trait':
        return getTraitImage(key);
      default:
        return undefined;
    }
  };

  const heading = options.heading ?? props.name;

  const handleChange = (key: string, value: number | undefined) => {
    const next = { ...(props.formData ?? {}) } as Record<string, number>;
    if (value === undefined) {
      delete next[key];
    } else {
      next[key] = value;
    }
    props.onChange(next);
  };

  return (
    <Stack spacing={2} mt={1}>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
          {heading}
        </Typography>
        <TextField
          size="small"
          label="Search"
          placeholder={options.searchPlaceholder}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          sx={{ minWidth: { xs: '100%', sm: 240 } }}
          disabled={entries.length === 0}
        />
      </Stack>

      {entries.length === 0 ? (
        <Typography color="text.secondary">No entries available to edit.</Typography>
      ) : filteredEntries.length === 0 ? (
        <Typography color="text.secondary">No entries match your search.</Typography>
      ) : (
        <>
          {!isSearching && filteredEntries.length > previewLimit ? (
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Showing first {previewLimit} of {filteredEntries.length} entries.
              </Typography>
              <Button variant="text" size="small" onClick={() => setShowAll((prev) => !prev)}>
                {showAll ? 'Show less' : 'Show all'}
              </Button>
            </Stack>
          ) : null}
          <Box sx={{ maxHeight: 420, overflowY: 'auto', pr: 1 }}>
            <Grid container columnSpacing={2} rowSpacing={1.5}>
              {visibleEntries.map(([key, value]) => (
                <Grid item xs={12} md={6} key={key}>
                  <Stack direction="row" spacing={1.5} alignItems="center">
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ minWidth: 180 }}>
                      {getAvatarSrc(key) ? (
                        <Avatar
                          src={getAvatarSrc(key)}
                          alt={key}
                          sx={{ width: 26, height: 26 }}
                          imgProps={options.imageType === 'champion' ? championAvatarImgProps : undefined}
                        />
                      ) : null}
                      <Typography sx={{ fontWeight: 600 }}>{key}</Typography>
                    </Stack>
                    {options.enumOptions ? (
                      <TextField
                        select
                        size="small"
                        label="Value"
                        value={value ?? ''}
                        onChange={(event) => handleChange(key, Number(event.target.value))}
                        fullWidth
                      >
                        {options.enumOptions.map((choice) => (
                          <MenuItem key={choice.value} value={choice.value}>
                            {choice.label}
                          </MenuItem>
                        ))}
                      </TextField>
                    ) : (
                      <TextField
                        type="number"
                        size="small"
                        label="Value"
                        value={value ?? ''}
                        inputProps={{ min: options.min }}
                        onChange={(event) => {
                          const newValue = event.target.value === '' ? undefined : Number(event.target.value);
                          handleChange(key, Number.isNaN(newValue) ? undefined : newValue);
                        }}
                        fullWidth
                      />
                    )}
                  </Stack>
                </Grid>
              ))}
            </Grid>
          </Box>
        </>
      )}
    </Stack>
  );
}

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
              <TableCell>
                <Stack direction="row" spacing={1} alignItems="center">
                  {getChampionImage(name) ? (
                    <Avatar
                      src={getChampionImage(name)}
                      alt={name}
                      sx={{ width: 28, height: 28 }}
                      imgProps={championAvatarImgProps}
                    />
                  ) : null}
                  <span>{name}</span>
                </Stack>
              </TableCell>
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
              <TableCell>
                <Stack direction="row" spacing={1} alignItems="center">
                  {getTraitImage(name) ? (
                    <Avatar src={getTraitImage(name)} alt={name} sx={{ width: 24, height: 24 }} />
                  ) : null}
                  <span>{name}</span>
                </Stack>
              </TableCell>
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
                  />
                  <CardContent>
                    <Stack spacing={1}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Traits
                        </Typography>
                        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                          {info?.traits?.map((trait) => (
                            <Chip
                              key={trait}
                              label={trait}
                              size="small"
                              avatar={
                                getTraitImage(trait) ? (
                                  <Avatar src={getTraitImage(trait)} alt={trait} sx={{ width: 24, height: 24 }} />
                                ) : undefined
                              }
                            />
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
                <Chip
                  key={trait}
                  label={`${trait}: ${count}`}
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
          {Object.keys(solution.emblems).length ? (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Emblems
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {Object.entries(solution.emblems).map(([trait, count]) => (
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

function App({ mode, onToggleColorMode }: AppProps) {
  const [formData, setFormData] = useState<ConfigData | undefined>();
  const formRef = useRef<CoreForm<any, any, any> | null>(null);

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

  const templates: FormProps['templates'] = useMemo(
    () => ({
      ButtonTemplates: {
        SubmitButton: (props) => {
          const isDisabled = (props as { disabled?: boolean }).disabled;
          return (
            <Box textAlign="right" mt={2}>
              <Button
                type="submit"
                variant="contained"
                disabled={isDisabled || runMutation.isPending}
                endIcon={runMutation.isPending ? <CircularProgress size={16} color="inherit" /> : undefined}
              >
                {runMutation.isPending ? 'Running…' : 'Run solver'}
              </Button>
            </Box>
          );
        },
      },
    }),
    [runMutation.isPending]
  );

  const fields = useMemo(
    () => ({
      mapping: MappingField,
    }),
    [],
  );

  const uiSchema = useMemo(
    () => ({
      emblem_start_counts: {
        'ui:field': 'mapping',
        'ui:options': {
          min: 0,
          heading: 'Emblems',
          searchPlaceholder: 'Search emblems…',
          imageType: 'emblem',
        },
      },
      required_traits_min: {
        'ui:field': 'mapping',
        'ui:options': {
          min: 0,
          heading: 'Trait minimums',
          searchPlaceholder: 'Search traits…',
          imageType: 'trait',
        },
      },
      required_champions: {
        'ui:field': 'mapping',
        'ui:options': {
          heading: 'Champions',
          searchPlaceholder: 'Search champions…',
          imageType: 'champion',
          enumOptions: [
            { value: -1, label: 'Ban (-1)' },
            { value: 0, label: 'Ignore (0)' },
            { value: 1, label: 'Require (1)' },
          ],
        },
      },
    }),
    [],
  );

  const handleRunClick = () => {
    formRef.current?.submit();
  };

  const isLoading = schemaQuery.isLoading || configQuery.isLoading;
  const hasError = schemaQuery.error || configQuery.error;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'flex-start', sm: 'center' }}
          spacing={2}
        >
          <Box>
            <Typography variant="h4" gutterBottom>
              Bronze for Life UI
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Edit the solver configuration via JSON Schema, then run Bronze for Life to view the resulting team, traits, and requirements.
            </Typography>
          </Box>
          <FormControlLabel
            control={<Switch checked={mode === 'dark'} onChange={onToggleColorMode} />}
            label={mode === 'dark' ? 'Dark mode' : 'Light mode'}
          />
        </Stack>

        <Card>
          <CardHeader title="Solver configuration" />
          <CardContent>
            {isLoading && <Loader />}
            {hasError && (
              <Alert severity="error">Failed to load schema or default config. Please ensure the API is running.</Alert>
            )}
            {!isLoading && !hasError && schemaQuery.data && formData ? (
              <Form
                ref={formRef}
                schema={schemaQuery.data}
                formData={formData}
                onChange={(event) => setFormData(event.formData)}
                onSubmit={(event) => runMutation.mutate(event.formData)}
                validator={validator}
                templates={templates}
                fields={fields}
                uiSchema={uiSchema}
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
            <Box mt={3} display="flex" justifyContent="flex-end">
              <Button
                variant="contained"
                onClick={handleRunClick}
                disabled={!formData || runMutation.isPending}
                endIcon={runMutation.isPending ? <CircularProgress size={16} color="inherit" /> : undefined}
              >
                {runMutation.isPending ? 'Running…' : 'Run solver'}
              </Button>
            </Box>
          </CardContent>
        </Card>

        {runMutation.data ? <ResultsSection response={runMutation.data} /> : null}
      </Stack>
    </Container>
  );
}

export default App;
