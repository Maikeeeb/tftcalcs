import { describe, expect, it } from 'vitest';
import { countTankItems, isTankItemBuild, normalizeKey } from '../utils/assets';

describe('asset utilities', () => {
  it('normalizes keys by removing punctuation and casing', () => {
    expect(normalizeKey('Sunfire Cape!')).toBe('sunfirecape');
    expect(normalizeKey('TFT16_Teemo')).toBe('tft16teemo');
  });

  it('counts tank items accurately', () => {
    expect(countTankItems(["Sunfire Cape", "Protector's Vow", 'Warmogs'])).toBe(3);
    expect(countTankItems(['Jeweled Gauntlet', 'Infinity Edge'])).toBe(0);
  });

  it('detects tank builds when at least half the items are defensive', () => {
    expect(isTankItemBuild(["Protector's Vow", 'Sunfire Cape', 'Infinity Edge'])).toBe(true);
    expect(isTankItemBuild(['Jeweled Gauntlet', 'Infinity Edge', 'Last Whisper'])).toBe(false);
    expect(isTankItemBuild([])).toBe(false);
  });
});
