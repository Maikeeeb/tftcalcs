import { Box, CircularProgress, Stack, Typography } from '@mui/material';

function Loader({ message }: { message?: string }) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
      <Stack direction="row" spacing={2} alignItems="center">
        <CircularProgress size={24} />
        <Typography variant="body2" color="text.secondary">
          {message || 'Loading…'}
        </Typography>
      </Stack>
    </Box>
  );
}

export default Loader;
