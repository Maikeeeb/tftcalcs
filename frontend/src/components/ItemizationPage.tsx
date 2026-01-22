import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { HelpOutline, PlayArrow } from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';

import ItemizationResults from './ItemizationResults';
import Loader from './Loader';
import DebugLogCard from './DebugLogCard';
import { ItemOption, ItemizationConfig, ItemizationReference, ItemizationRunResponse } from '../types';
import { getItemizationConfig, getItemizationData, runItemization } from '../services/api';

const normalizeConfig = (config: Partial<ItemizationConfig> | undefined): ItemizationConfig => ({
  available_components: config?.available_components ?? [],
  available_completed_items: config?.available_completed_items ?? [],
  target_carries: config?.target_carries ?? [],
  team_traits: config?.team_traits ?? [],
  needed_traits: config?.needed_traits ?? [],
  allow_reforge: config?.allow_reforge ?? false,
});

const buildCounts = (items: string[]) =>
  items.reduce<Record<string, number>>((acc, item) => {
    acc[item] = (acc[item] ?? 0) + 1;
    return acc;
  }, {});

const InventoryPicker = ({
  label,
  options,
  values,
  onChange,
}: {
  label: string;
  options: ItemOption[];
  values: string[];
  onChange: (next: string[]) => void;
}) => {
  const [selection, setSelection] = useState<ItemOption | null>(null);
  const counts = useMemo(() => buildCounts(values), [values]);
  const nameMap = useMemo(
    () =>
      options.reduce<Record<string, string>>((acc, option) => {
        acc[option.apiName] = option.name;
        return acc;
      }, {}),
    [options],
  );

  const handleAdd = () => {
    if (!selection) return;
    onChange([...values, selection.apiName]);
    setSelection(null);
  };

  const handleRemoveOne = (apiName: string) => {
    const index = values.indexOf(apiName);
    if (index === -1) return;
    const next = [...values];
    next.splice(index, 1);
    onChange(next);
  };

  return (
    <Stack spacing={1.5}>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
        <Autocomplete
          value={selection}
          options={options}
          getOptionLabel={(option) => option.name}
          onChange={(_, value) => setSelection(value)}
          renderInput={(params) => <TextField {...params} label={label} />}
          fullWidth
        />
        <Button variant="outlined" onClick={handleAdd} disabled={!selection}>
          Add
        </Button>
      </Stack>
      <Stack direction="row" spacing={1} flexWrap="wrap">
        {Object.entries(counts).length ? (
          Object.entries(counts).map(([apiName, count]) => (
            <Chip
              key={apiName}
              label={`${nameMap[apiName] ?? apiName} ×${count}`}
              onDelete={() => handleRemoveOne(apiName)}
              size="small"
            />
          ))
        ) : (
          <Typography variant="body2" color="text.secondary">
            No items selected yet.
          </Typography>
        )}
      </Stack>
    </Stack>
  );
};

const ItemizationPage = () => {
  const [config, setConfig] = useState<ItemizationConfig>(normalizeConfig(undefined));

  const configQuery = useQuery({
    queryKey: ['itemization-config'],
    queryFn: getItemizationConfig,
  });
  const dataQuery = useQuery({
    queryKey: ['itemization-data'],
    queryFn: getItemizationData,
  });

  const runMutation = useMutation({
    mutationFn: runItemization,
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
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          Itemization Finder
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Enter your available components and completed items to find which carries can build their ideal items. The
          tool ranks champions based on how close they are to their optimal builds.
        </Typography>
      </Box>

      <Card>
        <CardHeader
          title="Inventory & Targets"
          subheader="Add components and completed items from your inventory, then select target carries to prioritize"
        />
        <CardContent>
          {isLoading && <Loader message="Loading itemization data…" />}
          {hasError && (
            <Alert severity="error">Failed to load itemization data. Please ensure the API is running.</Alert>
          )}
          {!isLoading && !hasError && reference ? (
            <Stack spacing={3}>
              <InventoryPicker
                label="Available components"
                options={reference.components}
                values={config.available_components}
                onChange={(next) => setConfig((prev) => ({ ...prev, available_components: next }))}
              />
              <InventoryPicker
                label="Available completed items"
                options={reference.completed_items}
                values={config.available_completed_items}
                onChange={(next) => setConfig((prev) => ({ ...prev, available_completed_items: next }))}
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
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Target carries (optional)"
                    helperText={
                      config.target_carries.length > 0
                        ? `Prioritizing ${config.target_carries.length} ${config.target_carries.length === 1 ? 'carry' : 'carries'}`
                        : 'Select specific carries to prioritize, or leave empty to see all options'
                    }
                  />
                )}
              />
              <Box
                sx={{
                  p: 2,
                  bgcolor: 'background.default',
                  borderRadius: 1,
                  border: 1,
                  borderColor: 'divider',
                }}
              >
                <Stack direction="row" spacing={1} alignItems="flex-start">
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.allow_reforge}
                        onChange={(event) => setConfig((prev) => ({ ...prev, allow_reforge: event.target.checked }))}
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2">
                          <strong>Allow reforging completed items</strong>
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block">
                          Consider breaking down completed items to craft better builds
                        </Typography>
                      </Box>
                    }
                  />
                  <Tooltip title="Reforging allows the solver to break down completed items into their component parts to potentially craft better item combinations">
                    <HelpOutline fontSize="small" color="action" sx={{ mt: 1 }} />
                  </Tooltip>
                </Stack>
              </Box>
              <Box
                sx={{
                  pt: 2,
                  borderTop: 1,
                  borderColor: 'divider',
                  display: 'flex',
                  justifyContent: 'flex-end',
                }}
              >
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => runMutation.mutate(config)}
                  disabled={runMutation.isPending || (config.available_components.length === 0 && config.available_completed_items.length === 0)}
                  startIcon={runMutation.isPending ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
                  sx={{ minWidth: 150 }}
                >
                  {runMutation.isPending ? 'Ranking…' : 'Rank Carries'}
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
          <CardHeader
            title="Ranked Carry Builds"
            subheader={`Showing ${runMutation.data.result.solution.ranked_candidates.length} ${runMutation.data.result.solution.ranked_candidates.length === 1 ? 'candidate' : 'candidates'} ranked by build completeness`}
          />
          <CardContent>
            <ItemizationResults result={runMutation.data.result} nameMap={nameMap} />
          </CardContent>
        </Card>
      ) : null}
    </Stack>
  );
};

export default ItemizationPage;
