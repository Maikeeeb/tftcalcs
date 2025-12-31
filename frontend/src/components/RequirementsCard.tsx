import { Alert, Card, CardContent, CardHeader, Stack } from '@mui/material';

import { SolverResponse } from '../types';
import RequirementTable from './RequirementTable';

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

export default RequirementsCard;
