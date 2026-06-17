from tools import search_listings

if __name__ == "__main__":
    # Test 1: should return results priced <= 30
    r1 = search_listings('vintage graphic tee', 'M', 30)
    print(f'Test 1: {len(r1)} results, prices: {[x["price"] for x in r1[:3]]}')
    if r1: print(f'  Top: {r1[0]["title"]}')

    # Test 2: no price filter
    r2 = search_listings('90s track jacket', 'M', None)
    print(f'Test 2: {len(r2)} results')
    if r2: print(f'  Top: {r2[0]["title"]}')

    # Test 3: should return empty
    r3 = search_listings('designer ballgown', 'XXS', 5)
    print(f'Test 3: {len(r3)} results (expect 0)')

    results = search_listings("vintage tee", size=None, max_price=50)
    print(results[:2])
