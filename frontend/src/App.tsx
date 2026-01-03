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
  Stack,
  Switch,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
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
import { AppProps, ConfigData, SolverResponse } from './types';
import championCosts from './data/champion_costs.json';
import unlockableChampions from './data/unlockable_champions.json';

class SolverRunError extends Error {
  status: number;
  debugLog?: string[];
  context?: Record<string, unknown>;

  constructor(message: string, status: number, debugLog?: string[], context?: Record<string, unknown>) {
    super(message);
    this.status = status;
    this.debugLog = debugLog;
    this.context = context;
  }
}

const API_BASE = 'http://localhost:8000';

const fetchJson = async <T,>(path: string): Promise<T> => {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch ${path}: ${res.statusText}`);
  }
  return (await res.json()) as T;
};

function App({ mode, onToggleColorMode }: AppProps) {
  const [formData, setFormData] = useState<ConfigData | undefined>();
  const [activeMode, setActiveMode] = useState<'bronze' | 'standard'>('bronze');
  const [mustHaveItemizedTank, setMustHaveItemizedTank] = useState(true);
  const formRef = useRef<CoreForm<any, any, any> | null>(null);

  const schemaQuery = useQuery({ queryKey: ['schema'], queryFn: () => fetchJson<Record<string, unknown>>('/schema') });
  const configQuery = useQuery({ queryKey: ['config'], queryFn: () => fetchJson<ConfigData>('/config') });

  useEffect(() => {
    if (configQuery.data) {
      const modeFromConfig =
        configQuery.data.mode === 'standard' || configQuery.data.mode === 'bronze'
          ? (configQuery.data.mode as 'bronze' | 'standard')
          : 'bronze';
      const mustHaveTankFromConfig =
        typeof configQuery.data.must_have_itemized_tank === 'boolean'
          ? (configQuery.data.must_have_itemized_tank as boolean)
          : true;
      setActiveMode(modeFromConfig);
      setMustHaveItemizedTank(mustHaveTankFromConfig);
      setFormData({ ...configQuery.data, mode: modeFromConfig, must_have_itemized_tank: mustHaveTankFromConfig });
    }
  }, [configQuery.data]);

  useEffect(() => {
    if (formData?.mode === 'standard' || formData?.mode === 'bronze') {
      setActiveMode(formData.mode);
    }
  }, [formData?.mode]);

  const runMutation = useMutation({
    mutationFn: async (data: ConfigData) => {
      const res = await fetch(`${API_BASE}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const rawText = await res.text();
      let payload: any;
      try {
        payload = rawText ? JSON.parse(rawText) : undefined;
      } catch {
        payload = undefined;
      }

      if (!res.ok) {
        const detail = payload?.detail ?? payload;
        const message =
          typeof detail === 'string'
            ? detail
            : detail?.error || detail?.message || rawText || 'Failed to run solver';
        const debugLog =
          detail && typeof detail === 'object' && 'debug_log' in detail ? (detail as { debug_log: string[] }).debug_log : undefined;
        const context = detail && typeof detail === 'object' && 'context' in detail ? (detail as { context: Record<string, unknown> }).context : undefined;
        throw new SolverRunError(message, res.status, debugLog, context);
      }

      if (payload) {
        return payload as SolverResponse;
      }

      return (await res.json()) as SolverResponse;
    },
  });

  const errorDebugLog = runMutation.error instanceof SolverRunError ? runMutation.error.debugLog : undefined;

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
          searchPlaceholder: 'Search champions…',
          imageType: 'champion',
          enumOptions: [
            { value: -1, label: 'Ban (-1)' },
            { value: 0, label: 'Ignore (0)' },
            { value: 1, label: 'Require (1)' },
          ],
          unlockableValues: unlockableChampions,
          championCosts,
        },
      },
      mode: { 'ui:widget': 'hidden' },
      metatft_traits_path: { 'ui:widget': 'hidden' },
      must_have_itemized_tank: { 'ui:widget': 'hidden' },
    }),
    [],
  );

  const handleModeToggle = (_: MouseEvent<HTMLElement>, value: 'bronze' | 'standard' | null) => {
    if (!value) return;
    setActiveMode(value);
    setFormData((prev) => ({ ...(prev ?? {}), mode: value }));
  };

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
              {activeMode === 'standard' ? 'Standard mode' : 'Bronze for Life'} UI
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              Edit the solver configuration via JSON Schema, then run the solver to view the resulting team, traits, and
              requirements.
            </Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Mode
              </Typography>
              <ToggleButtonGroup
                color="primary"
                value={activeMode}
                exclusive
                onChange={handleModeToggle}
                size="small"
              >
                <ToggleButton value="bronze">Bronze for Life</ToggleButton>
                <ToggleButton value="standard">Standard</ToggleButton>
              </ToggleButtonGroup>
            </Stack>
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
                onChange={(event) => setFormData({ ...event.formData, must_have_itemized_tank: mustHaveItemizedTank })}
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
            {errorDebugLog?.length ? (
              <Box mt={2}>
                <DebugLogCard lines={errorDebugLog} />
              </Box>
            ) : null}
            <Box
              mt={3}
              display="flex"
              justifyContent="space-between"
              alignItems="center"
              flexDirection={{ xs: 'column', sm: 'row' }}
              gap={1.5}
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
                label="Must have itemized tank"
              />
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

        {runMutation.data ? (
          <ResultsSection response={runMutation.data} mustHaveItemizedTank={mustHaveItemizedTank} />
        ) : null}
      </Stack>
    </Container>
  );
}

export default App;
