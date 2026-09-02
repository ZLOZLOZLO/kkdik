"""kkdik — Türkiye KKDİK madde envanteri için istemci kütüphanesi.

Veri kaynağı: https://kkdik.ai/ (açık API, anahtar gerekmez)
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable, Iterator

__version__ = "0.1.0"
__all__ = [
    "Madde",
    "madde",
    "maddeler",
    "KkdikHatasi",
    "MaddeBulunamadi",
    "GECICI_KAYIT_SON_TARIHI",
    "GENEL_TAKVIM",
]

API = "https://kkdik.ai/wp-json/kkdik/v1"
KULLANICI_AJANI = f"kkdik-py/{__version__} (+https://kkdik.ai/)"

#: Bakanlık duyurusu: tonajdan bağımsız geçici kayıt son tarihi.
GECICI_KAYIT_SON_TARIHI = date(2026, 9, 30)

#: RG 23.12.2023 / 32408 ile belirlenen kademeli tam kayıt takvimi.
GENEL_TAKVIM = (
    (1000.0, date(2026, 12, 31)),
    (100.0, date(2028, 12, 31)),
    (1.0, date(2030, 12, 31)),
)

#: CMR 1A/1B veya sucul akut 1 / kronik 1 maddeler için erken tarih.
ERKEN_SON_TARIH = date(2026, 12, 31)
ERKEN_ESIK_TON = 1.0


class KkdikHatasi(Exception):
    """Kütüphanenin tüm hatalarının atası."""


class MaddeBulunamadi(KkdikHatasi):
    """Verilen CAS numarası envanterde yok."""


def _cek(yol: str, zaman_asimi: float = 20.0) -> dict:
    istek = urllib.request.Request(
        f"{API}{yol}", headers={"User-Agent": KULLANICI_AJANI, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(istek, timeout=zaman_asimi) as yanit:
            return json.loads(yanit.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise MaddeBulunamadi(yol) from e
        raise KkdikHatasi(f"API {e.code} döndürdü: {yol}") from e
    except urllib.error.URLError as e:
        raise KkdikHatasi(f"kkdik.ai'ye ulaşılamadı: {e.reason}") from e


def _tarih(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def _liste(s: str | None) -> list[str]:
    if not s:
        return []
    return [p.strip() for p in s.split(",") if p.strip()]


@dataclass(frozen=True)
class Madde:
    """Envanterdeki tek bir kimyasal madde."""

    cas: str
    ec: str | None = None
    ad: str | None = None
    cmr_1a_1b: bool = False
    sucul_akut1_kronik1: bool = False
    son_tarih: date | None = None
    esik: str | None = None
    sebep: str | None = None
    zararlilik_kodlari: list[str] = field(default_factory=list)
    siniflandirma: list[str] = field(default_factory=list)
    url: str | None = None
    ham: dict = field(default_factory=dict, repr=False)

    @classmethod
    def _sozlukten(cls, d: dict) -> "Madde":
        return cls(
            cas=d.get("cas", ""),
            ec=d.get("ec") or None,
            ad=d.get("ad") or None,
            cmr_1a_1b=bool(d.get("cmr_1a_1b")),
            sucul_akut1_kronik1=bool(d.get("sucul_akut1_kronik1")),
            son_tarih=_tarih(d.get("erken_kayit_son_tarihi")),
            esik=d.get("erken_tarih_esigi") or None,
            sebep=d.get("erken_tarih_sebebi") or None,
            zararlilik_kodlari=_liste(d.get("zararlilik_ifade_kodlari")),
            siniflandirma=_liste(d.get("harmonize_siniflandirma")),
            url=d.get("url") or None,
            ham=d,
        )

    @property
    def erken_tarihli(self) -> bool:
        """Madde CMR 1A/1B ya da sucul akut 1 / kronik 1 mi?"""
        return self.cmr_1a_1b or self.sucul_akut1_kronik1

    def son_tarih_tonaj(self, ton_yil: float) -> date | None:
        """Yıllık tonaja göre bu maddenin tam kayıt son tarihi.

        1 ton/yıl altındaki maddeler kayıt kapsamı dışındadır; ``None`` döner.
        """
        if ton_yil < 1.0:
            return None
        if self.erken_tarihli and ton_yil >= ERKEN_ESIK_TON:
            return ERKEN_SON_TARIH
        for esik, tarih in GENEL_TAKVIM:
            if ton_yil >= esik:
                return tarih
        return None

    def kalan_gun(self, ton_yil: float, bugun: date | None = None) -> int | None:
        """Tam kayıt son tarihine kalan gün. Süre dolduysa negatif değer döner."""
        hedef = self.son_tarih_tonaj(ton_yil)
        if hedef is None:
            return None
        return (hedef - (bugun or date.today())).days

    def gecici_kayit_kalan_gun(self, bugun: date | None = None) -> int:
        """30 Eylül 2026 geçici kayıt tarihine kalan gün."""
        return (GECICI_KAYIT_SON_TARIHI - (bugun or date.today())).days


def madde(cas: str) -> Madde:
    """Tek bir CAS numarasını sorgular.

    >>> madde("71-43-2").ad
    'benzen'
    """
    cas = cas.strip()
    if not cas:
        raise ValueError("CAS numarası boş olamaz")
    return Madde._sozlukten(_cek("/cas/" + urllib.parse.quote(cas, safe="")))


def maddeler(cas_listesi: Iterable[str], hatalari_atla: bool = True) -> Iterator[Madde]:
    """Birden çok CAS numarasını sırayla sorgular.

    ``hatalari_atla`` açıkken envanterde bulunmayan numaralar atlanır.
    """
    for cas in cas_listesi:
        try:
            yield madde(cas)
        except MaddeBulunamadi:
            if not hatalari_atla:
                raise
