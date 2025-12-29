import { MouseEvent, useEffect, useMemo, useRef, useState } from 'react';
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
  ToggleButton,
  ToggleButtonGroup,
  PaletteMode,
  Tooltip,
  TextField as MuiTextField,
} from '@mui/material';
import { CheckCircle, ContentCopy } from '@mui/icons-material';
import Form from '@rjsf/mui';
import validator from '@rjsf/validator-ajv8';
import { FieldProps } from '@rjsf/utils';
import type CoreForm from '@rjsf/core';
import type { FormProps } from '@rjsf/core';
import { useMutation, useQuery } from '@tanstack/react-query';
import { buildTeamPlannerCode, getTeamPlannerSlotCount } from './teamPlanner';

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
const itemImages: Record<string, string> = {};

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

  const directChampionMatch = filename.match(/TFT\d+_(.+?)\.TFT_Set\d+\.png$/);
  if (directChampionMatch && !filename.includes('_splash')) {
    championImages[normalizeKey(directChampionMatch[1])] = url;
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

  const itemMatch = filename.match(/TFT_Item_(.+?)(?:\.TFT_Set\d+)?\.png/i);
  if (itemMatch) {
    itemImages[normalizeKey(itemMatch[1])] = url;
    return;
  }

  if (normalizedFilename.includes('arcanist')) {
    traitImages.arcanist = url;
  }
});

aliasIfMissing('arcanist', ['sorcerer'], emblemImages);
aliasIfMissing('arcanist', ['sorcerer'], traitImages);

const legacyItemAliases: Record<string, string[]> = {
  handofjustice: ['unstableconcoction'],
  voidstaff: ['statikkshiv'],
  giantslayer: ['madredsbloodrazor'],
  strikersflail: ['powergauntlet'],
  redbuff: ['rapidfirecannon'],
  sunfire: ['redbuff'],
  nashorstooth: ['leviathan'],
  edgeofnight: ['guardianangel'],
  steadfastheart: ['nightharvester'],
  evenshroud: ['spectralgauntlet'],
};

Object.entries(legacyItemAliases).forEach(([target, sources]) => {
  aliasIfMissing(target, sources, itemImages);
});

const itemImageRemaps: Record<string, string> = {
  sunfirecape: 'redbuff',
  sunfire: 'redbuff',
  spiritvisage: 'redemption',
  redbuff: 'rapidfirecannon',
};

Object.entries(itemImageRemaps).forEach(([target, source]) => {
  if (itemImages[source]) {
    itemImages[target] = itemImages[source];
  }
});

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
const getItemImage = (name: string) => itemImages[normalizeKey(name)];

const TANK_ITEM_NAMES = new Set(
  [
    'sunfire cape',
    'warmogs',
    'gargoyles',
    'spirit visage',
    'evenshroud',
    "protector's vow",
    'protectors vow',
    'bramble vest',
    'dragon claw',
    'adaptive helm',
    'steadfast heart',
    'ionic spark',
  ].map((name) => normalizeKey(name)),
);

const countTankItems = (items: string[] | undefined) =>
  (items ?? []).reduce((total, item) => (TANK_ITEM_NAMES.has(normalizeKey(item)) ? total + 1 : total), 0);

const isTankItemBuild = (items: string[] | undefined) => {
  const totalItems = items?.length ?? 0;
  if (!totalItems) return false;
  const tankCount = countTankItems(items);
  return tankCount >= Math.ceil(totalItems / 2);
};

type SolverResponse = {
  context: Record<string, unknown> & { mode?: 'bronze' | 'standard' };
  meta: {
    enabled: boolean;
    weights: {
      w_win: number;
      w_avg: number;
      w_freq: number;
    };
    unit_stats?: Record<string, { avg?: number; win?: number; freq?: number }>;
    trait_stats_enabled?: boolean;
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
      metatft?: { avg?: number; win?: number; freq?: number; items?: string[] } | null;
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
  mustHaveItemizedTank,
}: {
  response: SolverResponse;
  mustHaveItemizedTank: boolean;
}) {
  const { solution, units, meta } = response;
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle');
  const teamPlannerCode = useMemo(() => buildTeamPlannerCode(solution.team), [solution.team]);

  useEffect(() => {
    setCopyStatus('idle');
  }, [teamPlannerCode.code]);

  const handleCopyCode = async () => {
    if (!teamPlannerCode.code) return;
    try {
      await navigator.clipboard.writeText(teamPlannerCode.code);
      setCopyStatus('copied');
      setTimeout(() => setCopyStatus('idle'), 2000);
    } catch (err) {
      console.error('Failed to copy team planner code', err);
      setCopyStatus('error');
    }
  };

  const { topUnits, topUnitItems } = useMemo(() => {
    const weightedScores = solution.team.map((unit, index) => {
      const stats =
        units[unit]?.metatft ?? (meta.unit_stats?.[unit] as SolverResponse['units'][string]['metatft']);
      const winScore = (stats?.win ?? 0) * (meta.weights.w_win ?? 1);
      const freqScore = (stats?.freq ?? 0) * (meta.weights.w_freq ?? 1);
      const avgScore = (stats?.avg ?? 0) * (meta.weights.w_avg ?? 1);
      const score = winScore + freqScore - avgScore;

      return { unit, score, items: stats?.items ?? [], index };
    });

    weightedScores.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.index - b.index;
    });
    const limit = Math.min(3, weightedScores.length);

    const tankCandidates = weightedScores.filter((entry) => isTankItemBuild(entry.items));
    const fallbackTankCandidates = weightedScores
      .map((entry) => ({ ...entry, tankCount: countTankItems(entry.items) }))
      .filter((entry) => entry.tankCount > 0)
      .sort((a, b) => {
        if (b.tankCount !== a.tankCount) return b.tankCount - a.tankCount;
        return b.score - a.score;
      });

    const chosenTank = mustHaveItemizedTank
      ? tankCandidates[0] ?? fallbackTankCandidates[0] ?? null
      : null;

    const selected: typeof weightedScores = [];
    if (chosenTank) {
      selected.push(chosenTank);
    }

    for (const entry of weightedScores) {
      if (selected.some((sel) => sel.unit === entry.unit)) continue;
      if (mustHaveItemizedTank && chosenTank && isTankItemBuild(entry.items)) continue;
      selected.push(entry);
      if (selected.length >= limit) break;
    }

    if (selected.length < limit) {
      for (const entry of weightedScores) {
        if (selected.some((sel) => sel.unit === entry.unit)) continue;
        selected.push(entry);
        if (selected.length >= limit) break;
      }
    }

    return {
      topUnits: new Set(selected.map((entry) => entry.unit)),
      topUnitItems: new Map(selected.map((entry) => [entry.unit, entry.items])),
    };
  }, [
    meta.unit_stats,
    meta.weights.w_avg,
    meta.weights.w_freq,
    meta.weights.w_win,
    mustHaveItemizedTank,
    solution.team,
    units,
  ]);

  const missingItemImages = new Set<string>();

  const rosterCards = solution.team.map((unit) => {
    const info = units[unit];
    const showItems = topUnits.has(unit) ? topUnitItems.get(unit) ?? [] : [];
    showItems.forEach((item) => {
      if (!getItemImage(item)) {
        missingItemImages.add(item);
      }
    });
    const metatftStats = info?.metatft ?? (meta.unit_stats?.[unit] as SolverResponse['units'][string]['metatft']);
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
            action={
              showItems.length ? (
                <Stack direction="row" spacing={0.5} alignItems="center" flexWrap="wrap">
                  {showItems.map((item) => (
                    <Tooltip title={item} key={`${unit}-${item}`}>
                      <Avatar
                        variant="rounded"
                        src={getItemImage(item)}
                        alt={item}
                        sx={{ width: 32, height: 32 }}
                      >
                        {getItemImage(item) ? null : item.slice(0, 2)}
                      </Avatar>
                    </Tooltip>
                  ))}
                </Stack>
              ) : null
            }
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
              {meta.enabled ? (
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    MetaTFT
                  </Typography>
                  {metatftStats ? (
                    <Stack direction="row" spacing={1}>
                      {'avg' in metatftStats && metatftStats.avg !== undefined && (
                        <Chip label={`Avg: ${metatftStats.avg.toFixed(2)}`} size="small" />
                      )}
                      {'win' in metatftStats && metatftStats.win !== undefined && (
                        <Chip label={`Win: ${metatftStats.win.toFixed(2)}`} size="small" />
                      )}
                      {'freq' in metatftStats && metatftStats.freq !== undefined && (
                        <Chip label={`Freq: ${metatftStats.freq.toFixed(2)}`} size="small" />
                      )}
                    </Stack>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No MetaTFT stats available for this unit.
                    </Typography>
                  )}
                </Box>
              ) : null}
            </Stack>
          </CardContent>
        </Card>
      </Grid>
    );
  });

  const missingItemsList = Array.from(missingItemImages).sort();

  return (
    <Card>
      <CardHeader title="Team roster" subheader={`Team power: ${solution.team_power.toFixed(2)}`} />
      <CardContent>
        <Stack spacing={2}>
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Team Planner import code
            </Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'flex-end' }}>
              <TextField
                label={`Code (${getTeamPlannerSlotCount()} slots)`}
                value={teamPlannerCode.code ?? 'Unavailable'}
                InputProps={{ readOnly: true }}
                fullWidth
                color={teamPlannerCode.missing.length || teamPlannerCode.trimmed ? 'warning' : 'primary'}
                helperText={
                  teamPlannerCode.missing.length || teamPlannerCode.trimmed
                    ? 'Some units could not be included in the code.'
                    : 'Copy this code to import the team in the League client team planner.'
                }
              />
              <Tooltip
                title={
                  teamPlannerCode.missing.length
                    ? `Missing mapping for: ${teamPlannerCode.missing.join(', ')}`
                    : teamPlannerCode.trimmed
                        ? `Limited to first ${getTeamPlannerSlotCount()} unique units.`
                        : 'Copy team code to clipboard'
                }
              >
                <span>
                  <Button
                    variant="outlined"
                    startIcon={copyStatus === 'copied' ? <CheckCircle /> : <ContentCopy />}
                    color={copyStatus === 'error' ? 'error' : 'primary'}
                    onClick={handleCopyCode}
                    disabled={!teamPlannerCode.code}
                  >
                    {copyStatus === 'copied' ? 'Copied!' : 'Copy code'}
                  </Button>
                </span>
              </Tooltip>
            </Stack>
            {teamPlannerCode.missing.length ? (
              <Alert severity="warning" sx={{ mt: 1 }}>
                Missing team planner mapping for: {teamPlannerCode.missing.join(', ')}.
              </Alert>
            ) : null}
            {teamPlannerCode.trimmed ? (
              <Alert severity="info" sx={{ mt: 1 }}>
                Only the first {getTeamPlannerSlotCount()} unique units are included in the code. Remove duplicates to
                include all champions.
              </Alert>
            ) : null}
            {copyStatus === 'error' ? (
              <Alert severity="error" sx={{ mt: 1 }}>
                Failed to copy the code. Please try again or copy it manually from the field.
              </Alert>
            ) : null}
          </Box>
          {missingItemsList.length ? (
            <Alert severity="warning" variant="outlined">
              Missing images for: {missingItemsList.join(', ')}. Please report this so we can add the art.
            </Alert>
          ) : null}
          <Grid container spacing={2}>
            {rosterCards}
          </Grid>
        </Stack>
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
            Mode: {(response.context.mode as string) ?? 'bronze'}
          </Typography>
          <Typography variant="body1">
            MetaTFT weights {meta.enabled ? 'enabled' : 'disabled'}
          </Typography>
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

function ResultsSection({ response, mustHaveItemizedTank }: { response: SolverResponse; mustHaveItemizedTank: boolean }) {
  return (
    <Stack spacing={3} mt={2} mb={4}>
      <TeamRoster response={response} mustHaveItemizedTank={mustHaveItemizedTank} />
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
      mode: { 'ui:widget': 'hidden' },
      metatft_traits_path: { 'ui:widget': 'hidden' },
      must_have_itemized_tank: { 'ui:widget': 'hidden' },
    }),
    [],
  );

  const handleModeToggle = (
    _: MouseEvent<HTMLElement>,
    value: 'bronze' | 'standard' | null,
  ) => {
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
              Edit the solver configuration via JSON Schema, then run the solver to view the resulting team, traits, and requirements.
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
