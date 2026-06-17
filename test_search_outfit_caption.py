from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

if __name__ == "__main__":
    item = search_listings('vintage graphic tee', 'M', 30)[0]
    print('Item:', item['title'])

    # Test suggest_outfit with wardrobe
    wardrobe = get_example_wardrobe()
    outfit = suggest_outfit(item, wardrobe)
    print('\nOutfit (with wardrobe):', outfit[:400], '...')

    # Test suggest_outfit empty wardrobe
    outfit_empty = suggest_outfit(item, get_empty_wardrobe())
    print('\nOutfit (empty wardrobe):', outfit_empty[:200], '...')

    # Test create_fit_card
    card = create_fit_card(outfit, item)
    print('\nFit card:', card[:200], '...')

    # Test fallback
    fallback = create_fit_card('', item)
    print('\nFallback card:', fallback)

    outfit = "Pair with baggy jeans and sneakers for a streetwear look."
    print(create_fit_card(outfit, item))

    print("=" * 70)
    print("TOOL 1: search_listings")
    print("=" * 70)

    print("\n✓ Test 1: search_listings('vintage graphic tee', size='M', max_price=30)")
    results1 = search_listings("vintage graphic tee", size="M", max_price=30)
    print(f"  Found {len(results1)} results")
    if results1:
        print(f"  Top result: {results1[0]['title']} — ${results1[0]['price']} ({results1[0]['size']})")
        valid_prices = all(r['price'] <= 30 for r in results1)
        valid_sizes = all('M' in r['size'].upper() or 'm' in r['size'].lower() for r in results1)
        print(f"  ✓ All prices ≤ $30: {valid_prices}")
        print(f"  ✓ All sizes match 'M': {valid_sizes}")

    print("\n✓ Test 2: search_listings('90s track jacket', size='M', max_price=None)")
    results2 = search_listings("90s track jacket", size="M", max_price=None)
    print(f"  Found {len(results2)} results")
    if results2:
        print(f"  Top result: {results2[0]['title']} — ${results2[0]['price']}")

    print("\n✓ Test 3: search_listings('designer ballgown', size='XXS', max_price=5)")
    results3 = search_listings("designer ballgown", size="XXS", max_price=5)
    print(f"  Found {len(results3)} results (expected 0)")
    print(f"  ✓ Returns empty list (no exception): {results3 == []}")

    print("=" * 70)
    print("TOOL 2: suggest_outfit")
    print("=" * 70)

    test_item = {
        "id": "lst_001",
        "title": "Vintage Band Tee",
        "description": "faded 90s band tee",
        "category": "tops",
        "style_tags": ["vintage", "grunge", "oversized"],
        "size": "M",
        "condition": "good",
        "price": 24.0,
        "colors": ["black", "grey"],
        "brand": "Fruit of the Loom",
        "platform": "Depop"
    }

    print("\n✓ Test 1: suggest_outfit(item, wardrobe) with populated wardrobe")
    wardrobe = get_example_wardrobe()
    print(f"  Wardrobe has {len(wardrobe['items'])} items")
    outfit1 = suggest_outfit(test_item, wardrobe)
    print(f"  Output length: {len(outfit1)} characters")
    print(f"  First 100 chars: {outfit1[:100]}...")
    print(f"  ✓ Returns non-empty string: {len(outfit1) > 0}")
    print(f"  ✓ Mentions item or wardrobe pieces: {'tee' in outfit1.lower() or 'jeans' in outfit1.lower()}")

    print("\n✓ Test 2: suggest_outfit(item, wardrobe) with empty wardrobe")
    empty_wardrobe = get_empty_wardrobe()
    print(f"  Wardrobe has {len(empty_wardrobe['items'])} items")
    outfit2 = suggest_outfit(test_item, empty_wardrobe)
    print(f"  Output length: {len(outfit2)} characters")
    print(f"  First 100 chars: {outfit2[:100]}...")
    print(f"  ✓ Returns non-empty string: {len(outfit2) > 0}")
    print(f"  ✓ Mentions the item: {'tee' in outfit2.lower() or 'band' in outfit2.lower()}")

    print("=" * 70)
    print("TOOL 3: create_fit_card")
    print("=" * 70)

    test_item = {
        "id": "lst_001",
        "title": "Vintage Band Tee",
        "description": "faded 90s band tee",
        "category": "tops",
        "style_tags": ["vintage", "grunge"],
        "size": "M",
        "condition": "good",
        "price": 24.0,
        "colors": ["black"],
        "brand": "Fruit of the Loom",
        "platform": "Depop"
    }

    outfit_text = "Pair with baggy dark-wash jeans and chunky white sneakers for a relaxed grunge look."

    print("\n✓ Test 1: create_fit_card(outfit, item) with valid outfit")
    caption1 = create_fit_card(outfit_text, test_item)
    print(f"  Caption length: {len(caption1)} characters")
    print(f"  Caption: {caption1}")
    print(f"  ✓ Returns non-empty string: {len(caption1) > 0}")
    print(f"  ✓ Mentions item name: {'band' in caption1.lower() or 'tee' in caption1.lower()}")
    print(f"  ✓ Mentions price: {'$' in caption1 or '24' in caption1}")

    print("\n✓ Test 2: create_fit_card('', item) with empty outfit")
    caption2 = create_fit_card("", test_item)
    print(f"  Caption length: {len(caption2)} characters")
    print(f"  Caption: {caption2}")
    print(f"  ✓ Returns non-empty string (fallback): {len(caption2) > 0}")
    print(f"  ✓ Never returns None or crashes: True")

    print("\n✓ Test 3: Variation test — multiple calls should produce different outputs")
    captions = [create_fit_card(outfit_text, test_item) for _ in range(3)]
    unique_count = len(set(captions))
    print(f"  Generated 3 captions, {unique_count} unique outputs")
    print(f"  Caption 1: {captions[0][:60]}...")
    print(f"  Caption 2: {captions[1][:60]}...")
    print(f"  Caption 3: {captions[2][:60]}...")
    print(f"  ✓ Outputs vary (temperature working): {unique_count > 1}")
