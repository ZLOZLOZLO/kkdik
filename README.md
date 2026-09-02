# kkdik

Türkiye'nin KKDİK envanterine erişim için resmî istemci kütüphaneleri — Python ve JavaScript.

[KKDİK](https://tr.wikipedia.org/wiki/KKD%C4%B0K) (Kimyasalların Kaydı, Değerlendirilmesi, İzni ve
Kısıtlanması Hakkında Yönetmelik), Türkiye'de kimyasal maddelerin imalatını, piyasaya arzını ve
kullanımını düzenleyen mevzuattır. Bu kütüphaneler, bir CAS numarasından yola çıkarak maddenin
zararlılık sınıflandırmasını ve **kayıt son tarihini** hesaplar.

Veri kaynağı: **[kkdik.ai](https://kkdik.ai/)** açık API'si — 6.212 madde.
API anahtarı gerekmez, kayıt gerekmez, ücretsizdir.

---

## Python

```bash
pip install kkdik
```

```python
from kkdik import madde

m = madde("71-43-2")

print(m.ad)                      # benzen
print(m.ec)                      # 200-753-7
print(m.cmr_1a_1b)               # True
print(m.son_tarih)               # datetime.date(2026, 12, 31)
print(m.esik)                    # '1 ton/yıl'
print(m.sebep)                   # 'CMR Kategori 1A/1B'
print(m.zararlilik_kodlari)      # ['H225', 'H350', 'H340', ...]
```

Yıllık tonajına göre kendi son tarihini sor:

```python
print(m.son_tarih_tonaj(250))    # datetime.date(2028, 12, 31)
print(m.kalan_gun(250))          # 848
```

Toplu tarama — elindeki madde listesini dosyadan geçir:

```python
from kkdik import maddeler

for m in maddeler(["71-43-2", "50-00-0", "108-88-3"]):
    print(m.cas, m.ad, m.son_tarih)
```

Komut satırından:

```bash
python -m kkdik 71-43-2
python -m kkdik --tonaj 250 --csv maddelerim.csv
```

## JavaScript / Node

```bash
npm install kkdik
```

```js
import { madde } from 'kkdik';

const m = await madde('71-43-2');
console.log(m.ad, m.sonTarih, m.kalanGun(250));
```

Tarayıcıda da çalışır (API CORS açıktır):

```html
<script type="module">
  import { madde } from 'https://cdn.jsdelivr.net/npm/kkdik/+esm';
  const m = await madde('71-43-2');
  document.body.textContent = `${m.ad}: son tarih ${m.sonTarih}`;
</script>
```

---

## Son tarih nasıl hesaplanıyor

KKDİK kayıt takvimi, 23 Aralık 2023 tarihli ve 32408 sayılı Resmî Gazete'de yayımlanan değişiklik
yönetmeliğiyle kademelendirilmiştir:

| Yıllık tonaj | Tam kayıt son tarihi |
|---|---|
| 1.000 ton ve üzeri | 31 Aralık 2026 |
| 100 – 1.000 ton | 31 Aralık 2028 |
| 1 – 100 ton | 31 Aralık 2030 |

**Erken tarih kuralı:** madde CMR Kategori 1A/1B ise ya da sucul akut 1 / kronik 1 sınıfındaysa,
tonajı 1 ton/yıl eşiğini geçtiği anda **31 Aralık 2026** tarihine tabi olur. Kütüphane bu kuralı
`son_tarih_tonaj()` içinde uygular.

Ayrıca Bakanlık, tonaj aralığından bağımsız olarak **geçici kayıtların 30 Eylül 2026'ya kadar**
tamamlanmasını duyurmuştur; bu tarih `kkdik.GECICI_KAYIT_SON_TARIHI` sabitinde bulunur.

## Lisans

Kod MIT lisanslıdır. Veri, kkdik.ai tarafından atıf verilmek koşuluyla serbestçe kullanılabilir.

## Kaynaklar

- Yönetmelik: [Resmî Gazete, 23.06.2017, sayı 30105 (Mükerrer)](https://www.resmigazete.gov.tr/eskiler/2017/06/20170623M1-18.htm)
- Takvim değişikliği: [Resmî Gazete, 23.12.2023, sayı 32408](https://www.resmigazete.gov.tr/eskiler/2023/12/20231223-9.htm)
- Geçici kayıt duyurusu: [Çevre, Şehircilik ve İklim Değişikliği Bakanlığı](https://kimyasallar.csb.gov.tr/kimyasal-kayit-surecinde-ilgili-hususlar/381)
- Veri: [kkdik.ai](https://kkdik.ai/) — hazırlayan [ONAY Mühendislik](https://onaymuhendislik.com/)
