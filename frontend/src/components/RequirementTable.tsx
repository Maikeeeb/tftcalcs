import { Avatar, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';

import { SolverResponse } from '../types';
import {
  championAvatarImgProps,
  getChampionImage,
  getTraitImage,
  stripTFTPrefix,
} from '../utils/assets';

function RequirementTable({ requirements }: { requirements: SolverResponse['requirements'] }) {
  // Filter to show only non-default requirements
  // Default: rule === 0 (ignore) for champions, minimum === 0 for traits
  const championEntries = Object.entries(requirements.champions || {}).filter(
    ([, detail]) => detail.rule !== 0,
  );
  const traitEntries = Object.entries(requirements.traits || {}).filter(
    ([, detail]) => detail.minimum !== 0,
  );

  if (championEntries.length === 0 && traitEntries.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No custom requirements set (all using defaults)
      </Typography>
    );
  }

  return (
    <Stack spacing={2}>
      {championEntries.length > 0 && (
        <>
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
                      <span>{stripTFTPrefix(name)}</span>
                    </Stack>
                  </TableCell>
                  <TableCell>{detail.status}</TableCell>
                  <TableCell>{detail.present ? 'Yes' : 'No'}</TableCell>
                  <TableCell>{detail.satisfied ? 'Satisfied' : 'Missing'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </>
      )}

      {traitEntries.length > 0 && (
        <>
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
        </>
      )}
    </Stack>
  );
}

export default RequirementTable;
