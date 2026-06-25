# 🚢 SeaRates Tracker

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-v1.0.0-orange)](https://pypi.org/project/searates-tracker/)

> 🇸🇦 مكتبة بايثون مفتوحة المصدر لتتبع الحاويات والشحنات عبر SeaRates API.
>
> 🇬🇧 Open-source Python library for tracking containers & shipments via SeaRates API.

---

## ✨ المميزات | Features

| 🚢 بحري | ✈️ جوي | 📦 بريدي | 🚂 سكك | 🚛 بري |
|:------:|:-----:|:-------:|:-----:|:-----:|
| ✅ | ✅ | ✅ | ✅ | ✅ |

- 🔍 تتبع الحاويات البحرية، بوليصة الشحن، والحجوزات
- ✈️ تتبع الشحن الجوي (AWB)
- 📦 تتبع الطرود البريدية (UPS, FedEx, DHL, USPS...)
- 🚂 تتبع شحنات السكك الحديدية
- 🚛 تتبع الشحن البري
- 🏷️ جلب قائمة 240+ شركة شحن بحري
- 🔎 البحث عن شركة الشحن من بادئة الحاوية
- 🌐 بناء روابط التتبع المباشر
- ⚡ يعمل بدون API key للتتبع البريدي وقائمة الشركات

---

## 📦 التثبيت | Installation

```bash
pip install searates-tracker
```

أو من المصدر:

```bash
git clone https://github.com/benchaa/searates-tracker.git
cd searates-tracker
pip install -e .
```

---

## 🚀 الاستخدام السريع | Quick Start

### ١. جلب قائمة شركات الشحن

```python
from searates_tracker import SeaRatesClient

client = SeaRatesClient()
carriers = client.get_carriers()

print(f"✅ {len(carriers)} شركة شحن مدعومة")

# عرض أول 5 شركات
for c in carriers[:5]:
    print(f"🚢 {c.name}: {c.scac_codes}")
```

**المخرجات:**
```
✅ 240 شركة شحن مدعومة
🚢 AC Container Line: ['ALRB']
🚢 Admiral Container Lines: ['ADMU']
🚢 Africa Express Line: ['AEXU']
...
```

---

### ٢. تتبع طرد بريدي (بدون API key)

```python
client = SeaRatesClient()

result = client.track_parcel("1Z9999999999999999")
print(f"📦 الناقل: {result.carrier_name}")  # UPS
print(f"📊 الحالة: {result.status_message}")
```

---

### ٣. تتبع حاوية بحرية (مع API key)

```python
client = SeaRatesClient(api_key="YOUR_API_KEY")

result = client.track_sea(
    number="MEDU3288655",
    sealine="MSCU",
    tracking_type="ct",  # ct=حاوية, bl=بوليصة, bk=حجز
    route=True,           # تفعيل تتبع المسار
)

print(f"📍 من: {result.direction_from}")
print(f"📍 إلى: {result.direction_to}")
print(f"📊 التقدم: {result.progress}%")
print(f"🕐 وصول متوقع: {result.eta}")

for event in result.events:
    print(f"   {event.date} | {event.event} | {event.location}")
```

---

### ٤. البحث عن شركة الشحن

```python
# بحث بالاسم
results = client.find_carrier("Maersk")
for c in results:
    print(f"🚢 {c.name}: SCAC={c.scac_codes}")

# تحديد شركة الشحن من بادئة الحاوية
carrier = client.find_carrier_by_prefix("MAEU9168137")
print(f"📦 {carrier.name}")  # Maersk
```

---

### ٥. رابط التتبع المباشر

```python
url = SeaRatesClient.get_public_tracking_url("MEDU3288655", "ct")
print(url)
# https://www.searates.com/container/tracking/?number=MEDU3288655&type=ct
```

---

## 📚 توثيق API | API Reference

### `SeaRatesClient`

| الطريقة | الوصف | API Key |
|---------|-------|:------:|
| `track_sea(number, sealine, type, route)` | تتبع حاوية بحرية | ⚠️ |
| `track_air(number)` | تتبع شحنة جوية | ⚠️ |
| `track_parcel(number)` | تتبع طرد بريدي | ❌ |
| `track_rail(number)` | تتبع شحنة سكة حديد | ❌ |
| `track_road(number)` | تتبع شحنة برية | ❌ |
| `get_carriers()` | قائمة شركات الشحن | ❌ |
| `find_carrier(query)` | بحث عن شركة شحن | ❌ |
| `find_carrier_by_prefix(number)` | تحديد الشركة من البادئة | ❌ |
| `get_public_tracking_url(number)` | رابط التتبع المباشر | ❌ |

### نماذج البيانات

| النموذج | الحقول الرئيسية |
|---------|----------------|
| `SeaTrackingResult` | `direction_from`, `direction_to`, `eta`, `progress`, `events`, `routes`, `vessels` |
| `ParcelTrackingResult` | `carrier_name`, `carrier_code`, `events` |
| `TrackingEvent` | `date`, `event`, `location`, `vessel`, `voyage` |
| `RoutePoint` | `from_name`, `to_name`, `path`, `atd`, `eta` |
| `Carrier` | `name`, `scac_codes`, `prefixes`, `active_types` |

---

## ⚠️ معالجة الأخطاء

```python
from searates_tracker import (
    SeaRatesClient,
    SeaRatesRateLimitError,
    SeaRatesNotFoundError,
    SeaRatesAuthError,
)

client = SeaRatesClient()

try:
    result = client.track_sea("BAD1234567", sealine="XXXX")
except SeaRatesNotFoundError:
    print("❌ رقم الحاوية غير موجود")
except SeaRatesRateLimitError:
    print("⚠️ تجاوزت حد الطلبات — سجل واحصل على API key")
except SeaRatesAuthError:
    print("🔑 API key غير صالح")
```

---

## 🏗️ هيكل المشروع

```
searates-tracker/
├── searates_tracker/
│   ├── __init__.py      # Exports
│   ├── client.py         # Main client
│   ├── models.py         # Data models
│   └── exceptions.py     # Custom exceptions
├── examples/
│   └── basic_usage.py    # Usage examples
├── pyproject.toml        # Package config
└── README.md
```

---

## 🔑 الحصول على API Key

1. سجل في [SeaRates.com](https://www.searates.com/)
2. اذهب إلى **Settings → API**
3. انسخ الـ API Token

```python
client = SeaRatesClient(api_key="sk_live_xxxxxxxxxxxxxxxx")
```

---

## 📄 الترخيص | License

MIT — استخدمها بحرية في مشاريعك التجارية والشخصية.

---

## 🤝 المساهمة | Contributing

الـ Issues والـ Pull Requests مرحب بها!

```bash
git clone https://github.com/benchaa/searates-tracker.git
cd searates-tracker
pip install -e ".[dev]"
pytest
```

---

**صنع بـ ❤️ — Mohammed Benchaa**
