import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation, useQuery } from '@tanstack/react-query';

import ItemizationResults from './ItemizationResults';
import Loader from './Loader';
import DebugLogCard from './DebugLogCard';
import { ItemizationConfig, ItemizationReference, ItemizationRunResponse } from '../types';

const API_BASE = 'http://localhost:8000';
const ITEMIZATION_VERSION = 2;

const fetchJson = async <T,>(path: string): Promise<T> => {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch ${path}: ${res.statusText}`);
  }
  return (await res.json()) as T;
};

const normalizeConfig = (config: Partial<ItemizationConfig> | undefined): ItemizationConfig => ({
  available_components: config?.available_components ?? [],
  available_completed_items: config?.available_completed_items ?? [],
  target_carries: config?.target_carries ?? [],
  team_traits: config?.team_traits ?? [],
  needed_traits: config?.needed_traits ?? [],
  allow_reforge: config?.allow_reforge ?? false,
});

const ItemizationPage = () => {
  const [config, setConfig] = useState<ItemizationConfig>(normalizeConfig(undefined));

  const configQuery = useQuery({
    queryKey: ['itemization-config'],
    queryFn: () => fetchJson<{ version: number; config: ItemizationConfig }>('/v2/itemization/config'),
  });
  const dataQuery = useQuery({
    queryKey: ['itemization-data'],
    queryFn: () => fetchJson<{ version: number; data: ItemizationReference }>('/v2/itemization/data'),
  });

  const runMutation = useMutation({
    mutationFn: async (payload: ItemizationConfig) => {
      const res = await fetch(`${API_BASE}/v2/itemization/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ version: ITEMIZATION_VERSION, config: { ...payload, mode: 'itemization' } }),
      });

      const rawText = await res.text();
      let parsed: any;
      try {
        parsed = rawText ? JSON.parse(rawText) : undefined;
      } catch {
        parsed = undefined;
      }

      if (!res.ok) {
        const detail = parsed?.detail ?? parsed ?? rawText;
        const message = typeof detail === 'string' ? detail : detail?.error || 'Failed to run itemization solver';
        throw new Error(message);
      }

      return parsed as ItemizationRunResponse;
    },
  });

  const hasError = configQuery.error || dataQuery.error;
  const isLoading = configQuery.isLoading || dataQuery.isLoading;

  const reference = dataQuery.data?.data;
  const nameMap = useMemo(() => runMutation.data?.result.items.names_by_api ?? {}, [runMutation.data]);

  useEffect(() => {
    if (configQuery.data?.config) {
      setConfig(normalizeConfig(configQuery.data.config));
    }
  }, [configQuery.data]);

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" gutterBottom>
          Itemization finder
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Enter your components and completed items to see which carries are closest to their ideal builds.
        </Typography>
      </Box>

      <Card>
        <CardHeader title="Inventory & targets" />
        <CardContent>
          {isLoading && <Loader />}
          {hasError && (
            <Alert severity="error">Failed to load itemization data. Please ensure the API is running.</Alert>
          )}
          {!isLoading && !hasError && reference ? (
            <Stack spacing={3}>
              <Autocomplete
                multiple
                options={reference.components}
                getOptionLabel={(option) => option.name}
                value={reference.components.filter((item) => config.available_components.includes(item.apiName))}
                onChange={(_, value) =>
                  setConfig((prev) => ({
                    ...prev,
                    available_components: value.map((item) => item.apiName),
                  }))
                }
                renderInput={(params) => <TextField {...params} label="Available components" />}
              />
              <Autocomplete
                multiple
                options={reference.completed_items}
                getOptionLabel={(option) => option.name}
                value={reference.completed_items.filter((item) => config.available_completed_items.includes(item.apiName))}
                onChange={(_, value) =>
                  setConfig((prev) => ({
                    ...prev,
                    available_completed_items: value.map((item) => item.apiName),
                  }))
                }
                renderInput={(params) => <TextField {...params} label="Available completed items" />}
              />
              <Autocomplete
                multiple
                options={reference.target_carries}
                getOptionLabel={(option) => option.name}
                value={reference.target_carries.filter((item) => config.target_carries.includes(item.apiName))}
                onChange={(_, value) =>
                  setConfig((prev) => ({
                    ...prev,
                    target_carries: value.map((item) => item.apiName),
                  }))
                }
                renderInput={(params) => <TextField {...params} label="Target carries (optional)" />}
              />
              <Autocomplete
                multiple
                options={reference.traits}
                value={config.team_traits}
                onChange={(_, value) => setConfig((prev) => ({ ...prev, team_traits: value }))}
                renderInput={(params) => <TextField {...params} label="Current team traits" />}
              />
              <Autocomplete
                multiple
                options={reference.traits}
                value={config.needed_traits}
                onChange={(_, value) => setConfig((prev) => ({ ...prev, needed_traits: value }))}
                renderInput={(params) => <TextField {...params} label="Needed traits" />}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.allow_reforge}
                    onChange={(event) => setConfig((prev) => ({ ...prev, allow_reforge: event.target.checked }))}
                  />
                }
                label="Allow reforging completed items"
              />
              <Box textAlign="right">
                <Button
                  variant="contained"
                  onClick={() => runMutation.mutate(config)}
                  disabled={runMutation.isPending}
                  endIcon={runMutation.isPending ? <CircularProgress size={16} color="inherit" /> : undefined}
                >
                  {runMutation.isPending ? 'Ranking…' : 'Rank carries'}
                </Button>
              </Box>
            </Stack>
          ) : null}
          {runMutation.error ? (
            <Alert severity="error" sx={{ mt: 2 }}>
              {(runMutation.error as Error).message}
            </Alert>
          ) : null}
          {runMutation.error && runMutation.error instanceof Error && runMutation.error.message ? (
            <Box mt={2}>
              <DebugLogCard lines={[runMutation.error.message]} />
            </Box>
          ) : null}
        </CardContent>
      </Card>

      {runMutation.data ? (
        <Card>
          <CardHeader title="Closest carry builds" />
          <CardContent>
            <ItemizationResults result={runMutation.data.result} nameMap={nameMap} />
          </CardContent>
        </Card>
      ) : null}
    </Stack>
  );
};

export default ItemizationPage;
