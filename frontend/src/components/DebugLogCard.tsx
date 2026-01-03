import { useMemo, useState } from 'react';

import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import { Box, Button, Card, CardContent, CardHeader, Stack, Typography } from '@mui/material';

type DebugLogCardProps = {
  lines?: string[];
};

function DebugLogCard({ lines }: DebugLogCardProps) {
  const [copied, setCopied] = useState(false);
  const logText = useMemo(() => (lines && lines.length ? lines.join('\n') : ''), [lines]);

  if (!logText) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(logText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy log', err);
    }
  };

  return (
    <Card>
      <CardHeader
        title="Solver debug log"
        subheader="Trace of beam search decisions and filters"
        action={
          <Button variant="outlined" size="small" startIcon={copied ? <CheckIcon /> : <ContentCopyIcon />} onClick={handleCopy}>
            {copied ? 'Copied' : 'Copy log'}
          </Button>
        }
      />
      <CardContent>
        <Stack spacing={1.5}>
          <Typography variant="body2" color="text.secondary">
            Recent solver steps are shown below; share this log when reporting issues.
          </Typography>
          <Box
            component="pre"
            sx={{
              bgcolor: 'background.default',
              borderRadius: 1,
              p: 1.5,
              maxHeight: 300,
              overflow: 'auto',
              fontFamily: 'monospace',
              fontSize: '0.85rem',
              whiteSpace: 'pre-wrap',
            }}
          >
            {logText}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default DebugLogCard;
