import '@testing-library/jest-dom';
import { vi } from 'vitest';

vi.mock('@mui/icons-material', () => ({
  __esModule: true,
  CheckCircle: () => null,
  ContentCopy: () => null,
}));
