/**
 * kkdik — Türkiye KKDİK madde envanteri istemcisi.
 * Veri kaynağı: https://kkdik.ai/ (açık API, anahtar gerekmez)
 */

const API = 'https://kkdik.ai/wp-json/kkdik/v1';

/** Bakanlık duyurusu: tonajdan bağımsız geçici kayıt son tarihi. */
export const GECICI_KAYIT_SON_TARIHI = '2026-09-30';

/** RG 23.12.2023 / 32408 ile belirlenen kademeli tam kayıt takvimi. */
export const GENEL_TAKVIM = [
  [1000, '2026-12-31'],
  [100, '2028-12-31'],
  [1, '2030-12-31'],
];

const ERKEN_SON_TARIH = '2026-12-31';
const ERKEN_ESIK_TON = 1;

export class KkdikHatasi extends Error {}
export class MaddeBulunamadi extends KkdikHatasi {}

function liste(s) {
  if (!s) return [];
  return String(s).split(',').map((p) => p.trim()).filter(Boolean);
}

function gunFarki(hedefISO, bugun) {
  const a = new Date(hedefISO + 'T00:00:00Z');
  const b = bugun ? new Date(bugun) : new Date();
  const b0 = Date.UTC(b.getUTCFullYear(), b.getUTCMonth(), b.getUTCDate());
  return Math.round((a.getTime() - b0) / 86400000);
}

export class Madde {
  constructor(ham) {
    this.ham = ham;
    this.cas = ham.cas || '';
    this.ec = ham.ec || null;
    this.ad = ham.ad || null;
    this.cmr1a1b = Boolean(ham.cmr_1a_1b);
    this.suculAkut1Kronik1 = Boolean(ham.sucul_akut1_kronik1);
    this.sonTarih = ham.erken_kayit_son_tarihi || null;
    this.esik = ham.erken_tarih_esigi || null;
    this.sebep = ham.erken_tarih_sebebi || null;
    this.zararlilikKodlari = liste(ham.zararlilik_ifade_kodlari);
    this.siniflandirma = liste(ham.harmonize_siniflandirma);
    this.url = ham.url || null;
  }

  /** Madde CMR 1A/1B ya da sucul akut 1 / kronik 1 mi? */
  get erkenTarihli() {
    return this.cmr1a1b || this.suculAkut1Kronik1;
  }

  /**
   * Yıllık tonaja göre tam kayıt son tarihi (ISO). Kapsam dışıysa null.
   * @param {number} tonYil
   */
  sonTarihTonaj(tonYil) {
    if (!(tonYil >= 1)) return null;
    if (this.erkenTarihli && tonYil >= ERKEN_ESIK_TON) return ERKEN_SON_TARIH;
    for (const [esik, tarih] of GENEL_TAKVIM) {
      if (tonYil >= esik) return tarih;
    }
    return null;
  }

  /** Tam kayıt son tarihine kalan gün; süre dolduysa negatif. */
  kalanGun(tonYil, bugun) {
    const hedef = this.sonTarihTonaj(tonYil);
    return hedef === null ? null : gunFarki(hedef, bugun);
  }

  /** 30 Eylül 2026 geçici kayıt tarihine kalan gün. */
  geciciKayitKalanGun(bugun) {
    return gunFarki(GECICI_KAYIT_SON_TARIHI, bugun);
  }
}

/**
 * Tek bir CAS numarasını sorgular.
 * @param {string} cas
 * @returns {Promise<Madde>}
 */
export async function madde(cas) {
  const temiz = String(cas || '').trim();
  if (!temiz) throw new TypeError('CAS numarası boş olamaz');

  let yanit;
  try {
    yanit = await fetch(`${API}/cas/${encodeURIComponent(temiz)}`, {
      headers: { Accept: 'application/json' },
    });
  } catch (e) {
    throw new KkdikHatasi(`kkdik.ai'ye ulaşılamadı: ${e.message}`);
  }
  if (yanit.status === 404) throw new MaddeBulunamadi(temiz);
  if (!yanit.ok) throw new KkdikHatasi(`API ${yanit.status} döndürdü: ${temiz}`);
  return new Madde(await yanit.json());
}

/**
 * Birden çok CAS numarasını sorgular. Bulunamayanlar atlanır.
 * @param {string[]} casListesi
 * @param {{esZamanli?: number, hatalariAtla?: boolean}} [secenekler]
 * @returns {Promise<Madde[]>}
 */
export async function maddeler(casListesi, secenekler = {}) {
  const { esZamanli = 4, hatalariAtla = true } = secenekler;
  const girdi = [...casListesi];
  const sonuc = [];
  let i = 0;

  async function isci() {
    while (i < girdi.length) {
      const cas = girdi[i++];
      try {
        sonuc.push(await madde(cas));
      } catch (e) {
        if (!(e instanceof MaddeBulunamadi) || !hatalariAtla) throw e;
      }
    }
  }

  await Promise.all(Array.from({ length: Math.max(1, esZamanli) }, isci));
  return sonuc;
}

export default { madde, maddeler, Madde, GECICI_KAYIT_SON_TARIHI, GENEL_TAKVIM };
