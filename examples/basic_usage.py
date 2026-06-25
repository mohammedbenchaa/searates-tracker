"""
SeaRates Tracker — أمثلة استخدام
=================================

هذا الملف يحتوي أمثلة عملية لاستخدام المكتبة.
"""

from searates_tracker import SeaRatesClient


def example_carriers():
    """🔍 جلب قائمة شركات الشحن المدعومة."""
    print("=" * 60)
    print("📋 شركات الشحن المدعومة")
    print("=" * 60)

    client = SeaRatesClient()
    carriers = client.get_carriers()

    print(f"✅ تم جلب {len(carriers)} شركة شحن\n")

    # عرض أول 10 شركات
    for c in carriers[:10]:
        scac = ", ".join(c.scac_codes[:3])
        prefixes = ", ".join(c.prefixes[:3]) or "-"
        print(f"  🚢 {c.name}")
        print(f"     SCAC: {scac} | Prefixes: {prefixes}")
        print(f"     CT:{c.supports_containers} BL:{c.supports_bl} BK:{c.supports_booking}")
        print()

    # إحصائيات
    active = sum(1 for c in carriers if c.active)
    maintenance = sum(1 for c in carriers if c.maintenance)
    print(f"📊 نشطة: {active} | صيانة: {maintenance}")


def example_search_carrier():
    """🔎 البحث عن شركة شحن."""
    print("\n" + "=" * 60)
    print("🔎 البحث عن شركة شحن")
    print("=" * 60)

    client = SeaRatesClient()

    # بحث باسم الشركة
    results = client.find_carrier("Maersk")
    for c in results:
        print(f"  🚢 {c.name}: {c.scac_codes}")

    # بحث بكود SCAC
    results = client.find_carrier("MSCU")
    for c in results:
        print(f"  🚢 {c.name}: {c.scac_codes}")

    # تحديد شركة الشحن من بادئة الحاوية
    carrier = client.find_carrier_by_prefix("MAEU9168137")
    if carrier:
        print(f"\n  📦 الحاوية MAEU9168137 → {carrier.name}")
        print(f"     SCAC: {carrier.scac_codes[0]}")


def example_track_parcel():
    """📦 تتبع طرد بريدي (يعمل بدون API key)."""
    print("\n" + "=" * 60)
    print("📦 تتبع طرد بريدي")
    print("=" * 60)

    client = SeaRatesClient()

    # تتبع طرد UPS (أي رقم 1Z...)
    result = client.track_parcel("1Z9999999999999999")
    print(f"  الرقم: {result.tracking_number}")
    print(f"  الناقل: {result.carrier_name} ({result.carrier_code})")
    print(f"  الحالة: {result.status_message}")


def example_track_sea():
    """🚢 تتبع حاوية بحرية (يحتاج API key)."""
    print("\n" + "=" * 60)
    print("🚢 تتبع حاوية بحرية")
    print("=" * 60)

    # مع API key
    client = SeaRatesClient(api_key="YOUR_API_KEY_HERE")

    try:
        result = client.track_sea(
            number="MEDU3288655",
            sealine="MSCU",
            tracking_type="ct",
            route=True,
        )

        print(f"  📦 {result.tracking_number}")
        print(f"  🚢 {result.sealine_name}")
        print(f"  📍 من: {result.direction_from}")
        print(f"  📍 إلى: {result.direction_to}")
        print(f"  📊 التقدم: {result.progress}%")
        print(f"  🕐 ETD: {result.etd} | ETA: {result.eta}")
        print(f"  📋 عدد الأحداث: {len(result.events)}")

        for event in result.events[:5]:
            print(f"     {event.date} | {event.event} | {event.location}")

        for route in result.routes[:3]:
            print(f"     Route: {route.from_name} → {route.to_name}")

    except Exception as e:
        print(f"  ❌ {e}")


def example_public_url():
    """🌐 رابط التتبع العام."""
    print("\n" + "=" * 60)
    print("🌐 روابط التتبع المباشر")
    print("=" * 60)

    url = SeaRatesClient.get_public_tracking_url("MEDU3288655", "ct")
    print(f"  🔗 {url}")


if __name__ == "__main__":
    example_carriers()
    example_search_carrier()
    example_track_parcel()
    example_public_url()
    # example_track_sea()  # يحتاج API key
