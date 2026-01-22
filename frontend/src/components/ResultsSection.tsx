import { Stack } from '@mui/material';

import { SolverResponse } from '../types';
import DebugLogCard from './DebugLogCard';
import MetaCard from './MetaCard';
import RequirementsCard from './RequirementsCard';
import TeamRoster from './TeamRoster';
import TraitsSummary from './TraitsSummary';

function ResultsSection({ response, mustHaveItemizedTank }: { response: SolverResponse; mustHaveItemizedTank: boolean }) {
  return (
    <Stack spacing={3} mt={3} mb={4}>
      <TeamRoster response={response} mustHaveItemizedTank={mustHaveItemizedTank} />
      <TraitsSummary response={response} />
      <RequirementsCard response={response} />
      <MetaCard response={response} />
      {response.debug_log && response.debug_log.length > 0 && (
        <DebugLogCard lines={response.debug_log} />
      )}
    </Stack>
  );
}

export default ResultsSection;
