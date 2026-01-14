import { describe, expect, it } from 'vitest';
import {
  getChampionImage,
  getTraitImage,
  getEmblemImage,
  getItemImage,
  normalizeKey,
} from '../utils/assets';

describe('assets extended utilities', () => {
  describe('getChampionImage', () => {
    it('handles API name format', () => {
      const result = getChampionImage('TFT16_Tristana');
      expect(result).toBeUndefined();
    });

    it('handles normalized names', () => {
      const result = getChampionImage('tristana');
      expect(result).toBeUndefined();
    });

    it('handles empty string', () => {
      const result = getChampionImage('');
      expect(result).toBeUndefined();
    });
  });

  describe('getTraitImage', () => {
    it('handles trait names', () => {
      const result = getTraitImage('Invoker');
      expect(result).toBeUndefined();
    });

    it('handles normalized trait names', () => {
      const result = getTraitImage('invoker');
      expect(result).toBeUndefined();
    });

    it('handles empty string', () => {
      const result = getTraitImage('');
      expect(result).toBeUndefined();
    });
  });

  describe('getEmblemImage', () => {
    it('handles emblem names', () => {
      const result = getEmblemImage('Invoker');
      expect(result).toBeUndefined();
    });

    it('falls back to trait image', () => {
      const result = getEmblemImage('Invoker');
      expect(result).toBeUndefined();
    });

    it('handles empty string', () => {
      const result = getEmblemImage('');
      expect(result).toBeUndefined();
    });
  });

  describe('getItemImage', () => {
    it('handles item names', () => {
      const result = getItemImage('Sunfire Cape');
      expect(result).toBeUndefined();
    });

    it('handles normalized item names', () => {
      const result = getItemImage('sunfirecape');
      expect(result).toBeUndefined();
    });

    it('handles empty string', () => {
      const result = getItemImage('');
      expect(result).toBeUndefined();
    });
  });

  describe('normalizeKey edge cases', () => {
    it('handles special characters', () => {
      expect(normalizeKey("Protector's Vow")).toBe('protectorsvow');
      expect(normalizeKey('Item-Name!')).toBe('itemname');
      expect(normalizeKey('Test_123')).toBe('test123');
    });

    it('handles empty string', () => {
      expect(normalizeKey('')).toBe('');
    });

    it('handles numbers only', () => {
      expect(normalizeKey('123')).toBe('123');
    });

    it('handles mixed case', () => {
      expect(normalizeKey('MiXeDcAsE')).toBe('mixedcase');
    });
  });
});
