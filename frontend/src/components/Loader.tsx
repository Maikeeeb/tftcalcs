import { CircularProgress, Stack, Typography } from '@mui/material';

function Loader() {
  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <CircularProgress size={20} />
      <Typography>Loading…</Typography>
    </Stack>
  );
}

export default Loader;
