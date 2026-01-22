import { useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import {
  Avatar,
  Box,
  Button,
  FormControlLabel,
  Grid,
  IconButton,
  InputAdornment,
  Stack,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import { Clear, Search, Block, RemoveCircle, CheckCircle } from '@mui/icons-material';
import { FieldProps } from '@rjsf/utils';

import { MappingFieldOptions } from '../types';
import {
  championAvatarImgProps,
  getChampionImage,
  getEmblemImage,
  getTraitImage,
  stripTFTPrefix,
} from '../utils/assets';

function MappingField(props: FieldProps<Record<string, number>>) {
  const options = (props.uiSchema?.['ui:options'] as MappingFieldOptions | undefined) ?? {};
  const entries = Object.entries(props.formData ?? {});
  const [search, setSearch] = useState('');
  const [showAll, setShowAll] = useState(false);
  const [showUnlockablesOnly, setShowUnlockablesOnly] = useState(false);
  const [costToggles, setCostToggles] = useState<Record<number, boolean>>({});
  const searchInputRef = useRef<HTMLInputElement>(null);

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

  // Fuzzy search function
  const fuzzyMatch = (text: string, query: string): boolean => {
    const normalizedText = text.toLowerCase();
    const normalizedQuery = query.toLowerCase().trim();
    
    if (!normalizedQuery) return true;
    
    // Exact match (case-insensitive)
    if (normalizedText.includes(normalizedQuery)) return true;
    
    // Fuzzy match: check if all query characters appear in order
    let textIndex = 0;
    for (const char of normalizedQuery) {
      const foundIndex = normalizedText.indexOf(char, textIndex);
      if (foundIndex === -1) return false;
      textIndex = foundIndex + 1;
    }
    return true;
  };

  const searchQuery = search.trim().toLowerCase();
  const searchedEntries = useMemo(() => {
    if (!searchQuery) return entries;
    
    return entries.filter(([key]) => {
      // Check champion name (with TFT prefix stripped for champions)
      const displayName = options.imageType === 'champion' ? stripTFTPrefix(key) : key;
      if (fuzzyMatch(displayName, searchQuery)) return true;
      
      // For champions, also check traits
      if (options.imageType === 'champion' && options.championTraits) {
        const traits = options.championTraits[key] || [];
        return traits.some((trait) => fuzzyMatch(trait, searchQuery));
      }
      
      return false;
    });
  }, [entries, searchQuery, options.imageType, options.championTraits]);

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

  // Keyboard shortcut: Ctrl/Cmd + K to focus search
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'k' && searchInputRef.current) {
        event.preventDefault();
        searchInputRef.current.focus();
        searchInputRef.current.select();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <Stack spacing={2} mt={1}>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'flex-start', md: 'center' }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, pt: { xs: 0, sm: 1 } }}>
          {heading}
        </Typography>
        <Box sx={{ flex: 1, minWidth: { xs: '100%', sm: 280 }, maxWidth: { sm: 500 } }}>
          <TextField
            inputRef={searchInputRef}
            size="small"
            fullWidth
            placeholder={options.searchPlaceholder || 'Search...'}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            disabled={entries.length === 0}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search fontSize="small" color="action" />
                </InputAdornment>
              ),
              endAdornment: search ? (
                <InputAdornment position="end">
                  <IconButton
                    size="small"
                    onClick={() => setSearch('')}
                    edge="end"
                    aria-label="clear search"
                    sx={{ p: 0.5 }}
                  >
                    <Clear fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ) : undefined,
            }}
            helperText={
              entries.length === 0
                ? 'No entries available'
                : search
                  ? `Found ${filteredEntries.length} matching ${filteredEntries.length === 1 ? 'entry' : 'entries'}`
                  : `Total: ${entries.length} ${entries.length === 1 ? 'entry' : 'entries'}`
            }
          />
        </Box>
        {options.imageType === 'champion' && availableCosts.length ? (
          <Stack
            direction="row"
            spacing={1}
            alignItems="center"
            flexWrap="wrap"
            useFlexGap
            sx={{ mt: { xs: 1, sm: 0 }, width: { xs: '100%', sm: 'auto' } }}
          >
            <Typography variant="body2" color="text.secondary" sx={{ minWidth: 'fit-content' }}>
              Cost filters:
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
                  {cost}-cost: {isEnabled ? 'Show' : 'Hide'}
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
            label={
              <Typography variant="body2">
                Unlockables only
                {showUnlockablesOnly && (
                  <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 0.5 }}>
                    ({filteredEntries.length})
                  </Typography>
                )}
              </Typography>
            }
            sx={{ mt: { xs: 1, sm: 0 } }}
          />
        ) : null}
      </Stack>

      {entries.length === 0 ? (
        <Box
          sx={{
            p: 3,
            textAlign: 'center',
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            bgcolor: 'background.default',
          }}
        >
          <Typography color="text.secondary" variant="body2">
            No entries available to edit.
          </Typography>
        </Box>
      ) : filteredEntries.length === 0 ? (
        <Box
          sx={{
            p: 3,
            textAlign: 'center',
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            bgcolor: 'background.default',
          }}
        >
          <Typography color="text.secondary" variant="body2" gutterBottom>
            No entries match your search.
          </Typography>
          <Button size="small" onClick={() => setSearch('')} sx={{ mt: 1 }}>
            Clear search
          </Button>
        </Box>
      ) : (
        <>
          {!isSearching && filteredEntries.length > previewLimit ? (
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              spacing={1}
              alignItems={{ sm: 'center' }}
              justifyContent="space-between"
              sx={{ p: 1.5, bgcolor: 'background.default', borderRadius: 1 }}
            >
              <Typography variant="body2" color="text.secondary">
                Showing {showAll ? 'all' : `first ${previewLimit}`} of {filteredEntries.length} entries
              </Typography>
              <Button variant="outlined" size="small" onClick={() => setShowAll((prev) => !prev)}>
                {showAll ? 'Show less' : `Show all (${filteredEntries.length})`}
              </Button>
            </Stack>
          ) : null}
          <Box
            sx={{
              maxHeight: 500,
              overflowY: 'auto',
              pr: 1,
              '&::-webkit-scrollbar': {
                width: 8,
              },
              '&::-webkit-scrollbar-track': {
                bgcolor: 'background.paper',
              },
              '&::-webkit-scrollbar-thumb': {
                bgcolor: 'divider',
                borderRadius: 1,
                '&:hover': {
                  bgcolor: 'text.secondary',
                },
              },
            }}
          >
            <Grid container columnSpacing={2} rowSpacing={1.5}>
              {visibleEntries.map(([key, value]) => (
                <Grid item xs={12} md={options.enumOptions ? 6 : 4} key={key}>
                  {options.enumOptions ? (
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ py: 0.5 }}>
                      <Stack
                        direction="row"
                        spacing={1}
                        alignItems="center"
                        sx={{ minWidth: { xs: 100, sm: 120 }, flex: 1 }}
                      >
                        {getAvatarSrc(key) ? (
                          <Avatar
                            src={getAvatarSrc(key)}
                            alt={key}
                            sx={{ width: 26, height: 26 }}
                            imgProps={options.imageType === 'champion' ? championAvatarImgProps : undefined}
                          />
                        ) : null}
                        <Typography sx={{ fontWeight: 500, fontSize: '0.9rem' }} noWrap>
                          {options.imageType === 'champion' ? stripTFTPrefix(key) : key}
                        </Typography>
                      </Stack>
                      <ToggleButtonGroup
                        value={value ?? 0}
                        exclusive
                        onChange={(_, newValue) => {
                          if (newValue !== null) {
                            handleChange(key, newValue);
                          }
                        }}
                        size="small"
                        sx={{ '& .MuiToggleButton-root': { px: 1, py: 0.5, minWidth: 'auto' } }}
                      >
                        {options.enumOptions.map((choice) => {
                          const icons: Record<number, ReactNode> = {
                            [-1]: <Block fontSize="small" />,
                            [0]: <RemoveCircle fontSize="small" />,
                            [1]: <CheckCircle fontSize="small" />,
                          };
                          const labels: Record<number, string> = {
                            [-1]: 'Ban',
                            [0]: 'Ignore',
                            [1]: 'Require',
                          };
                          return (
                            <ToggleButton key={choice.value} value={choice.value}>
                              <Tooltip title={choice.label} arrow>
                                <Stack direction="row" spacing={0.5} alignItems="center">
                                  {icons[choice.value as keyof typeof icons]}
                                  <Typography variant="caption" sx={{ display: { xs: 'none', sm: 'block' } }}>
                                    {labels[choice.value as keyof typeof labels]}
                                  </Typography>
                                </Stack>
                              </Tooltip>
                            </ToggleButton>
                          );
                        })}
                      </ToggleButtonGroup>
                    </Stack>
                  ) : (
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ py: 0.5 }}>
                      <Stack
                        direction="row"
                        spacing={1}
                        alignItems="center"
                        sx={{ minWidth: { xs: 120, sm: 140 }, flex: 1 }}
                      >
                        {getAvatarSrc(key) ? (
                          <Avatar
                            src={getAvatarSrc(key)}
                            alt={key}
                            sx={{ width: 26, height: 26 }}
                            imgProps={options.imageType === 'champion' ? championAvatarImgProps : undefined}
                          />
                        ) : null}
                        <Typography sx={{ fontWeight: 500, fontSize: '0.9rem' }} noWrap>
                          {options.imageType === 'champion' ? stripTFTPrefix(key) : key}
                        </Typography>
                      </Stack>
                      <TextField
                        type="number"
                        size="small"
                        value={value ?? ''}
                        inputProps={{ min: options.min, style: { textAlign: 'center' } }}
                        onChange={(event) => {
                          const newValue = event.target.value === '' ? undefined : Number(event.target.value);
                          handleChange(key, Number.isNaN(newValue) ? undefined : newValue);
                        }}
                        sx={{ width: { xs: '100%', sm: 80 } }}
                      />
                    </Stack>
                  )}
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
