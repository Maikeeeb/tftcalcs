import {
  ConfigData,
  ItemizationConfig,
  ItemizationReference,
  ItemizationRunResponse,
  SolverResponse,
} from '../types';

// API base URL from environment variable, with fallback to default
export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Itemization API version
const ITEMIZATION_VERSION = 2;

/**
 * Custom error class for solver run errors with debug information
 */
export class SolverRunError extends Error {
  status: number;
  debugLog?: string[];
  context?: Record<string, unknown>;

  constructor(message: string, status: number, debugLog?: string[], context?: Record<string, unknown>) {
    super(message);
    this.name = 'SolverRunError';
    this.status = status;
    this.debugLog = debugLog;
    this.context = context;
  }
}

/**
 * Generic helper to fetch JSON from the API
 */
async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch ${path}: ${res.statusText}`);
  }
  return (await res.json()) as T;
}

/**
 * Get the JSON schema for solver configuration
 */
export async function getSchema(): Promise<Record<string, unknown>> {
  return fetchJson<Record<string, unknown>>('/schema');
}

/**
 * Get the default solver configuration
 */
export async function getDefaultConfig(): Promise<ConfigData> {
  return fetchJson<ConfigData>('/config');
}

/**
 * Run the solver with the provided configuration
 */
export async function runSolver(config: ConfigData): Promise<SolverResponse> {
  const res = await fetch(`${API_BASE}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });

  const rawText = await res.text();
  let payload: any;
  try {
    payload = rawText ? JSON.parse(rawText) : undefined;
  } catch {
    payload = undefined;
  }

  if (!res.ok) {
    const detail = payload?.detail ?? payload;
    const message =
      typeof detail === 'string'
        ? detail
        : detail?.error || detail?.message || rawText || 'Failed to run solver';
    const debugLog =
      detail && typeof detail === 'object' && 'debug_log' in detail
        ? (detail as { debug_log: string[] }).debug_log
        : undefined;
    const context =
      detail && typeof detail === 'object' && 'context' in detail
        ? (detail as { context: Record<string, unknown> }).context
        : undefined;
    throw new SolverRunError(message, res.status, debugLog, context);
  }

  if (payload) {
    return payload as SolverResponse;
  }

  return (await res.json()) as SolverResponse;
}

/**
 * Get the itemization schema
 */
export async function getItemizationSchema(): Promise<{ version: number; schema: Record<string, unknown> }> {
  return fetchJson<{ version: number; schema: Record<string, unknown> }>('/v2/itemization/schema');
}

/**
 * Get the default itemization configuration
 */
export async function getItemizationConfig(): Promise<{ version: number; config: ItemizationConfig }> {
  return fetchJson<{ version: number; config: ItemizationConfig }>('/v2/itemization/config');
}

/**
 * Get reference data for itemization UI (components, items, carries, traits)
 */
export async function getItemizationData(): Promise<{ version: number; data: ItemizationReference }> {
  return fetchJson<{ version: number; data: ItemizationReference }>('/v2/itemization/data');
}

/**
 * Run the itemization solver with the provided configuration
 */
export async function runItemization(config: ItemizationConfig): Promise<ItemizationRunResponse> {
  const res = await fetch(`${API_BASE}/v2/itemization/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ version: ITEMIZATION_VERSION, config: { ...config, mode: 'itemization' } }),
  });

  const rawText = await res.text();
  let parsed: any;
  try {
    parsed = rawText ? JSON.parse(rawText) : undefined;
  } catch {
    parsed = undefined;
  }

  if (!res.ok) {
    const detail = parsed?.detail ?? parsed ?? rawText;
    const message = typeof detail === 'string' ? detail : detail?.error || 'Failed to run itemization solver';
    throw new Error(message);
  }

  return parsed as ItemizationRunResponse;
}
