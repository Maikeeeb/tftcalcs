import { useEffect, useMemo, useState } from 'react';
import { Avatar, Box, Button, FormControlLabel, Grid, MenuItem, Stack, Switch, TextField, ToggleButton, Typography } from '@mui/material';
import { FieldProps } from '@rjsf/utils';

import { MappingFieldOptions } from '../types';
import { championAvatarImgProps, getChampionImage, getEmblemImage, getTraitImage } from '../utils/assets';

function MappingField(props: FieldProps<Record<string, number>>) {
  const options = (props.uiSchema?.['ui:options'] as MappingFieldOptions | undefined) ?? {};
  const entries = Object.entries(props.formData ?? {});
  const [search, setSearch] = useState('');
  const [showAll, setShowAll] = useState(false);
  const [showUnlockablesOnly, setShowUnlockablesOnly] = useState(false);
  const [costToggles, setCostToggles] = useState<Record<number, boolean>>({});

  const unlockableSet = useMemo(() => new Set(options.unlockableValues ?? []), [options.unlockableValues]);
  const costMap = options.championCosts ?? {};

  const availableCosts = useMemo(() => {
    const costs = new Set<number>();
    entries.forEach(([key]) => {
      const cost = costMap[key];
      if (typeof cost === 'number') {
        costs.add(cost);
      }
    });
    return Array.from(costs).sort((a, b) => a - b);
  }, [costMap, entries]);

  useEffect(() => {
    setCostToggles((prev) => {
      const next = { ...prev } as Record<number, boolean>;
      let changed = false;
      availableCosts.forEach((cost) => {
        if (next[cost] === undefined) {
          next[cost] = true;
          changed = true;
        }
      });
      return changed ? next : prev;
    });
  }, [availableCosts]);

  const searchedEntries = entries.filter(([key]) => key.toLowerCase().includes(search.toLowerCase().trim()));

  const filteredEntries = showUnlockablesOnly
    ? searchedEntries.filter(([key]) => unlockableSet.has(key))
    : searchedEntries;

  const previewLimit = 20;
  const isSearching = search.trim().length > 0;
  const visibleEntries = isSearching || showAll ? filteredEntries : filteredEntries.slice(0, previewLimit);

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

  const applyCostToggle = (cost: number, enabled: boolean) => {
    if (!options.championCosts) return;
    const targetValue = enabled ? 0 : -1;
    const next = { ...(props.formData ?? {}) } as Record<string, number>;
    let changed = false;

    entries.forEach(([key, value]) => {
      if (unlockableSet.has(key)) return;
      if (options.championCosts?.[key] !== cost) return;
      if (value === 1) return;

      if (next[key] !== targetValue) {
        next[key] = targetValue;
        changed = true;
      }
    });

    if (changed) {
      props.onChange(next);
    }
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
        {options.imageType === 'champion' && availableCosts.length ? (
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
            <Typography variant="body2" color="text.secondary">
              Cost filters
            </Typography>
            {availableCosts.map((cost) => {
              const isEnabled = costToggles[cost] ?? true;
              return (
                <ToggleButton
                  key={`cost-${cost}`}
                  size="small"
                  value={cost}
                  selected={isEnabled}
                  onChange={() => {
                    const nextEnabled = !isEnabled;
                    setCostToggles((prev) => ({ ...prev, [cost]: nextEnabled }));
                    applyCostToggle(cost, nextEnabled);
                  }}
                  aria-label={`Toggle ${cost}-cost champions`}
                >
                  {cost}-cost: {isEnabled ? 'Ignore' : 'Ban'}
                </ToggleButton>
              );
            })}
          </Stack>
        ) : null}
        {options.unlockableValues?.length ? (
          <FormControlLabel
            control={
              <Switch
                size="small"
                checked={showUnlockablesOnly}
                onChange={(event) => setShowUnlockablesOnly(event.target.checked)}
              />
            }
            label="Unlockables only"
          />
        ) : null}
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

export default MappingField;
