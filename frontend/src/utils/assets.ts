const normalizeKey = (value: string) => value.toLowerCase().replace(/[^a-z0-9]/g, '');

const assetModules = import.meta.env?.VITEST
  ? {}
  : import.meta.glob('../tft-images/*', {
      eager: true,
      query: '?url',
      import: 'default',
    });

const championImages: Record<string, string> = {};
const traitImages: Record<string, string> = {};
const emblemImages: Record<string, string> = {};
const itemImages: Record<string, string> = {};

export const championAvatarImgProps = { style: { objectPosition: '70% 50%' } } as const;

const aliasIfMissing = (
  targetKey: string,
  sourceKeys: string[],
  imageMap: Record<string, string>,
) => {
  if (imageMap[targetKey]) return;
  for (const source of sourceKeys) {
    if (imageMap[source]) {
      imageMap[targetKey] = imageMap[source];
      return;
    }
  }
};

Object.entries(assetModules).forEach(([path, urlValue]) => {
  const filename = path.split('/').pop() ?? '';
  const url = urlValue as string;
  const normalizedFilename = normalizeKey(filename);

  const championMatch = filename.match(/TFT\d+_(.+?)_splash/);
  if (championMatch) {
    championImages[normalizeKey(championMatch[1])] = url;
    return;
  }

  const directChampionMatch = filename.match(/TFT\d+_(.+?)\.TFT_Set\d+\.png$/);
  if (directChampionMatch && !filename.includes('_splash')) {
    championImages[normalizeKey(directChampionMatch[1])] = url;
    return;
  }

  const emblemMatch = filename.match(/TFT\d+_Item_(.+?)EmblemItem/);
  if (emblemMatch) {
    emblemImages[normalizeKey(emblemMatch[1])] = url;
    return;
  }

  const traitMatch = filename.match(/Trait_Icon_\d+_(.+?)\./);
  if (traitMatch) {
    traitImages[normalizeKey(traitMatch[1])] = url;
    return;
  }

  const itemMatch = filename.match(/TFT_Item_(.+?)(?:\.TFT_Set\d+)?\.png/i);
  if (itemMatch) {
    itemImages[normalizeKey(itemMatch[1])] = url;
    return;
  }

  if (normalizedFilename.includes('arcanist')) {
    traitImages.arcanist = url;
  }
});

aliasIfMissing('arcanist', ['sorcerer'], emblemImages);
aliasIfMissing('arcanist', ['sorcerer'], traitImages);

const legacyItemAliases: Record<string, string[]> = {
  handofjustice: ['unstableconcoction'],
  voidstaff: ['statikkshiv'],
  giantslayer: ['madredsbloodrazor'],
  strikersflail: ['powergauntlet'],
  redbuff: ['rapidfirecannon'],
  sunfire: ['redbuff'],
  nashorstooth: ['leviathan'],
  edgeofnight: ['guardianangel'],
  steadfastheart: ['nightharvester'],
  evenshroud: ['spectralgauntlet'],
};

Object.entries(legacyItemAliases).forEach(([target, sources]) => {
  aliasIfMissing(target, sources, itemImages);
});

const itemImageRemaps: Record<string, string> = {
  sunfirecape: 'redbuff',
  sunfire: 'redbuff',
  spiritvisage: 'redemption',
  redbuff: 'rapidfirecannon',
  protectorsvow: 'frozenheart',
  krakensfury: 'runaanshurricane',
  kraken: 'runaanshurricane',
};

Object.entries(itemImageRemaps).forEach(([target, source]) => {
  if (itemImages[source]) {
    itemImages[target] = itemImages[source];
  }
});

export const getChampionImage = (name: string) => {
  const normalized = normalizeKey(name);
  const apiNameMatch = normalized.match(/^tft\d+(.*)$/);
  const candidates = [normalized];

  if (apiNameMatch?.[1]) {
    candidates.push(apiNameMatch[1]);
  }

  for (const candidate of candidates) {
    if (championImages[candidate]) {
      return championImages[candidate];
    }
  }

  return undefined;
};

export const getTraitImage = (name: string) => traitImages[normalizeKey(name)];
export const getEmblemImage = (name: string) => emblemImages[normalizeKey(name)] ?? traitImages[normalizeKey(name)];
export const getItemImage = (name: string) => itemImages[normalizeKey(name)];

const TANK_ITEM_NAMES = new Set(
  [
    'sunfire cape',
    'warmogs',
    'gargoyles',
    'spirit visage',
    'evenshroud',
    "protector's vow",
    'protectors vow',
    'bramble vest',
    'dragon claw',
    'adaptive helm',
    'steadfast heart',
    'ionic spark',
  ].map((name) => normalizeKey(name)),
);

export const countTankItems = (items: string[] | undefined) =>
  (items ?? []).reduce((total, item) => (TANK_ITEM_NAMES.has(normalizeKey(item)) ? total + 1 : total), 0);

export const isTankItemBuild = (items: string[] | undefined) => {
  const totalItems = items?.length ?? 0;
  if (!totalItems) return false;
  const tankCount = countTankItems(items);
  return tankCount >= Math.ceil(totalItems / 2);
};

export { normalizeKey };
