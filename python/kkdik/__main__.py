"""Komut satırı arayüzü:  python -m kkdik 71-43-2"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date

from . import GECICI_KAYIT_SON_TARIHI, KkdikHatasi, MaddeBulunamadi, madde


def _yaz(m, tonaj: float | None) -> None:
    print(f"{m.cas}  {m.ad or '(ad yok)'}")
    if m.ec:
        print(f"  EC numarası      : {m.ec}")
    if m.siniflandirma:
        print(f"  Sınıflandırma    : {', '.join(m.siniflandirma)}")
    if m.zararlilik_kodlari:
        print(f"  Zararlılık kodu  : {', '.join(m.zararlilik_kodlari)}")
    if m.erken_tarihli:
        print(f"  Erken tarih      : evet ({m.sebep}, eşik {m.esik})")
    if tonaj is not None:
        hedef = m.son_tarih_tonaj(tonaj)
        if hedef is None:
            print(f"  {tonaj:g} ton/yıl  : kayıt kapsamı dışında")
        else:
            kalan = m.kalan_gun(tonaj)
            print(f"  {tonaj:g} ton/yıl  : tam kayıt {hedef} ({kalan} gün)")
    print(f"  Geçici kayıt     : {GECICI_KAYIT_SON_TARIHI} "
          f"({(GECICI_KAYIT_SON_TARIHI - date.today()).days} gün)")
    if m.url:
        print(f"  Ayrıntı          : {m.url}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="kkdik",
        description="Türkiye KKDİK envanterinde CAS numarası sorgular. Veri: https://kkdik.ai/",
    )
    ap.add_argument("cas", nargs="*", help="Bir veya daha çok CAS numarası")
    ap.add_argument("--tonaj", type=float, metavar="TON",
                    help="Yıllık tonaj; son tarih buna göre hesaplanır")
    ap.add_argument("--csv", metavar="DOSYA",
                    help="Sonuçları CSV olarak bu dosyaya yaz")
    a = ap.parse_args(argv)

    if not a.cas:
        ap.print_help()
        return 2

    bulunanlar = []
    cikis = 0
    for cas in a.cas:
        try:
            m = madde(cas)
        except MaddeBulunamadi:
            print(f"{cas}: envanterde bulunamadı", file=sys.stderr)
            cikis = 1
            continue
        except KkdikHatasi as e:
            print(f"hata: {e}", file=sys.stderr)
            return 1
        bulunanlar.append(m)
        if not a.csv:
            _yaz(m, a.tonaj)
            print()

    if a.csv and bulunanlar:
        with open(a.csv, "w", newline="", encoding="utf-8-sig") as f:
            y = csv.writer(f)
            y.writerow(["CAS", "EC", "Ad", "Sınıflandırma", "Zararlılık kodları",
                        "CMR 1A/1B", "Sucul akut1/kronik1", "Son tarih"])
            for m in bulunanlar:
                hedef = m.son_tarih_tonaj(a.tonaj) if a.tonaj is not None else m.son_tarih
                y.writerow([m.cas, m.ec or "", m.ad or "",
                            "; ".join(m.siniflandirma), "; ".join(m.zararlilik_kodlari),
                            "evet" if m.cmr_1a_1b else "hayır",
                            "evet" if m.sucul_akut1_kronik1 else "hayır",
                            hedef or ""])
        print(f"{len(bulunanlar)} satır yazıldı: {a.csv}")

    return cikis


if __name__ == "__main__":
    raise SystemExit(main())
