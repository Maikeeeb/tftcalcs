import { MouseEvent, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Container,
  FormControlLabel,
  IconButton,
  Stack,
  Switch,
  Tab,
  Tabs,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import { Brightness4, Brightness7, PlayArrow } from '@mui/icons-material';
import Form from '@rjsf/mui';
import validator from '@rjsf/validator-ajv8';
import type CoreForm from '@rjsf/core';
import type { FormProps } from '@rjsf/core';
import { useMutation, useQuery } from '@tanstack/react-query';

import MappingField from './components/MappingField';
import ResultsSection from './components/ResultsSection';
import Loader from './components/Loader';
import DebugLogCard from './components/DebugLogCard';
import RootObjectFieldTemplate from './components/RootObjectFieldTemplate';
import ItemizationPage from './components/ItemizationPage';
import ErrorBoundary from './components/ErrorBoundary';
import { AppProps, ConfigData, SolverResponse } from './types';
import championCosts from './data/champion_costs.json';
import unlockableChampions from './data/unlockable_champions.json';
import { getSchema, getDefaultConfig, runSolver, SolverRunError, getChampions } from './services/api';

const RYZE_API_NAME = 'TFT16_Ryze';
const REGION_TRAITS = [
  'Bilgewater',
  'Demacia',
  'Freljord',
  'Ionia',
  'Ixtal',
  'Noxus',
  'Piltover',
  'Shadow Isles',
  'Shurima',
  'Targon',
  'Void',
  'Yordle',
  'Zaun',
] as const;

const asNumber = (value: unknown): number | undefined => (typeof value === 'number' ? value : undefined);
const asRecord = (value: unknown): Record<string, number> | undefined =>
  value && typeof value === 'object' ? (value as Record<string, number>) : undefined;

const applyRyzeDefaultsToFormData = (data?: ConfigData): ConfigData => {
  const baseData: ConfigData = { ...(data ?? {}) };
  const required = { ...(asRecord(data?.required_champions) ?? {}) };

  if (!(RYZE_API_NAME in required)) {
    required[RYZE_API_NAME] = 1;
  }

  baseData.required_champions = required;
  baseData.team_size = asNumber(data?.team_size) ?? 9;
  baseData.mode = 'ryze';

  return baseData;
};

function App({ mode, onToggleColorMode }: AppProps) {
  const [formData, setFormData] = useState<ConfigData | undefined>();
  const [activeMode, setActiveMode] = useState<'bronze' | 'standard' | 'ryze'>('bronze');
  const [mustHaveItemizedTank, setMustHaveItemizedTank] = useState(true);
  const [activeTab, setActiveTab] = useState<'comp' | 'itemization'>('comp');
  const formRef = useRef<CoreForm<any, any, any> | null>(null);

  const schemaQuery = useQuery({ queryKey: ['schema'], queryFn: getSchema });
  const configQuery = useQuery({ queryKey: ['config'], queryFn: getDefaultConfig });
  const championsQuery = useQuery({ queryKey: ['champions'], queryFn: getChampions });

  useEffect(() => {
    if (configQuery.data) {
      const modeFromConfig =
        configQuery.data.mode === 'standard' || configQuery.data.mode === 'bronze' || configQuery.data.mode === 'ryze'
          ? (configQuery.data.mode as 'bronze' | 'standard' | 'ryze')
          : 'bronze';
      const mustHaveTankFromConfig =
        typeof configQuery.data.must_have_itemized_tank === 'boolean'
          ? (configQuery.data.must_have_itemized_tank as boolean)
          : true;
      let nextFormData: ConfigData = {
        ...configQuery.data,
        mode: modeFromConfig,
        must_have_itemized_tank: mustHaveTankFromConfig,
      };

      if (modeFromConfig === 'ryze') {
        nextFormData = applyRyzeDefaultsToFormData(nextFormData);
      }

      setActiveMode(modeFromConfig);
      setMustHaveItemizedTank(mustHaveTankFromConfig);
      setFormData(nextFormData);
    }
  }, [configQuery.data]);

  useEffect(() => {
    if (formData?.mode === 'standard' || formData?.mode === 'bronze' || formData?.mode === 'ryze') {
      setActiveMode(formData.mode);
    }
  }, [formData?.mode]);

  const runMutation = useMutation({
    mutationFn: runSolver,
  });

  const debugLogLines = runMutation.error instanceof SolverRunError ? runMutation.error.debugLog : undefined;

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
      ObjectFieldTemplate: RootObjectFieldTemplate,
    }),
    [runMutation.isPending],
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
          searchPlaceholder: 'Search champions or traits (e.g., "tristana" or "yordle")…',
          imageType: 'champion',
          enumOptions: [
            { value: -1, label: 'Ban (-1)' },
            { value: 0, label: 'Ignore (0)' },
            { value: 1, label: 'Require (1)' },
          ],
          unlockableValues: unlockableChampions,
          championCosts,
          championTraits: championsQuery.data
            ? championsQuery.data.champions.reduce<Record<string, string[]>>(
                (acc, champ) => {
                  acc[champ.apiName] = champ.traits;
                  return acc;
                },
                {},
              )
            : undefined,
        },
      },
      mode: { 'ui:widget': 'hidden' },
      metatft_traits_path: { 'ui:widget': 'hidden' },
      must_have_itemized_tank: { 'ui:widget': 'hidden' },
      available_components: { 'ui:widget': 'hidden' },
      available_completed_items: { 'ui:widget': 'hidden' },
      target_carries: { 'ui:widget': 'hidden' },
      team_traits: { 'ui:widget': 'hidden' },
      needed_traits: { 'ui:widget': 'hidden' },
      allow_reforge: { 'ui:widget': 'hidden' },
    }),
    [championsQuery.data],
  );

  const handleModeToggle = (_: MouseEvent<HTMLElement>, value: 'bronze' | 'standard' | 'ryze' | null) => {
    if (!value) return;
    setActiveMode(value);
    if (value === 'ryze') {
      setFormData((prev) => applyRyzeDefaultsToFormData(prev));
      return;
    }

    setFormData((prev) => ({ ...(prev ?? {}), mode: value }));
  };

  const handleRunClick = () => {
    formRef.current?.submit();
  };

  const isLoading = schemaQuery.isLoading || configQuery.isLoading;
  const hasError = schemaQuery.error || configQuery.error;

  return (
    <ErrorBoundary>
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Stack spacing={3}>
          {/* Header */}
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            justifyContent="space-between"
            alignItems={{ xs: 'flex-start', sm: 'center' }}
            spacing={2}
          >
            <Box>
              <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
                TFT Calculator
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Find optimal team compositions and itemization strategies
              </Typography>
            </Box>
            <Tooltip title={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>
              <IconButton onClick={onToggleColorMode} color="inherit" aria-label="toggle theme">
                {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
              </IconButton>
            </Tooltip>
          </Stack>

          {/* Main Navigation Tabs */}
          <Tabs
            value={activeTab}
            onChange={(_, value) => setActiveTab(value)}
            textColor="primary"
            indicatorColor="primary"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab value="comp" label="Comp Finder" />
            <Tab value="itemization" label="Itemization" />
          </Tabs>

        {activeTab === 'comp' ? (
          <>
            {/* Mode Selector Section */}
            <Card variant="outlined">
              <CardContent>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Solver Mode
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Choose the solving mode that matches your strategy
                    </Typography>
                  </Box>
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
                    <Typography variant="body2" color="text.secondary" sx={{ minWidth: 60 }}>
                      Mode:
                    </Typography>
                    <ToggleButtonGroup
                      color="primary"
                      value={activeMode}
                      exclusive
                      onChange={handleModeToggle}
                      size="small"
                      fullWidth={false}
                    >
                      <ToggleButton value="bronze">Bronze for Life</ToggleButton>
                      <ToggleButton value="ryze">Ryze</ToggleButton>
                      <ToggleButton value="standard">Standard</ToggleButton>
                    </ToggleButtonGroup>
                  </Stack>
                  {activeMode === 'ryze' ? (
                    <Alert severity="info" icon={false} sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        <strong>Ryze mode:</strong> Counts only origin traits ({REGION_TRAITS.join(', ')}). Ryze is
                        required by default and boards use a level 9 team size unless overridden.
                      </Typography>
                    </Alert>
                  ) : activeMode === 'bronze' ? (
                    <Alert severity="info" icon={false} sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        <strong>Bronze for Life:</strong> Optimizes for traits active exactly at their first breakpoint,
                        focusing on bronze trait activation.
                      </Typography>
                    </Alert>
                  ) : (
                    <Alert severity="info" icon={false} sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        <strong>Standard mode:</strong> General-purpose team composition solver without bronze trait
                        constraints.
                      </Typography>
                    </Alert>
                  )}
                </Stack>
              </CardContent>
            </Card>
            <Card>
              <CardHeader
                title="Configuration"
                subheader="Adjust champion requirements, trait minimums, and emblems to customize your team search"
              />
              <CardContent>
                {isLoading && <Loader message="Loading configuration…" />}
                {hasError && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    <Typography variant="body2" gutterBottom>
                      <strong>Failed to load configuration</strong>
                    </Typography>
                    <Typography variant="body2">
                      Please ensure the API is running on port 8000. Check the console for more details.
                    </Typography>
                  </Alert>
                )}
                {!isLoading && !hasError && schemaQuery.data && formData ? (
                  <Form
                    ref={formRef}
                    schema={schemaQuery.data}
                    formData={formData}
                    onChange={(event) =>
                      setFormData({ ...event.formData, must_have_itemized_tank: mustHaveItemizedTank })
                    }
                    onSubmit={(event) =>
                      runMutation.mutate({
                        ...event.formData,
                        must_have_itemized_tank: mustHaveItemizedTank,
                      })
                    }
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
                {debugLogLines?.length ? (
                  <Box mt={2}>
                    <DebugLogCard lines={debugLogLines} />
                  </Box>
                ) : null}
                <Box
                  mt={3}
                  pt={3}
                  sx={{ borderTop: 1, borderColor: 'divider' }}
                  display="flex"
                  justifyContent="space-between"
                  alignItems="center"
                  flexDirection={{ xs: 'column', sm: 'row' }}
                  gap={2}
                >
                  <FormControlLabel
                    control={
                      <Switch
                        checked={mustHaveItemizedTank}
                        onChange={(event) => {
                          setMustHaveItemizedTank(event.target.checked);
                          setFormData((prev) => ({
                            ...(prev ?? {}),
                            must_have_itemized_tank: event.target.checked,
                          }));
                        }}
                      />
                    }
                    label={
                      <Typography variant="body2">
                        <strong>Require itemized tank</strong>
                        <Typography variant="caption" display="block" color="text.secondary">
                          Ensure at least one unit has tank items
                        </Typography>
                      </Typography>
                    }
                  />
                  <Button
                    variant="contained"
                    size="large"
                    onClick={handleRunClick}
                    disabled={!formData || runMutation.isPending}
                    startIcon={runMutation.isPending ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
                    sx={{ minWidth: 150 }}
                  >
                    {runMutation.isPending ? 'Running…' : 'Run Solver'}
                  </Button>
                </Box>
              </CardContent>
            </Card>

            {runMutation.data ? (
              <ResultsSection response={runMutation.data} mustHaveItemizedTank={mustHaveItemizedTank} />
            ) : null}
          </>
        ) : (
          <ItemizationPage />
        )}
        </Stack>
      </Container>
    </ErrorBoundary>
  );
}

export default App;
