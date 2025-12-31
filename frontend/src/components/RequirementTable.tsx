import { Avatar, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';

import { SolverResponse } from '../types';
import { championAvatarImgProps, getChampionImage, getTraitImage } from '../utils/assets';

function RequirementTable({ requirements }: { requirements: SolverResponse['requirements'] }) {
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

export default RequirementTable;
