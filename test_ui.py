from app import handle_query

if __name__ == "__main__":
    # Test 1: Happy path
    listing, outfit, fit_card = handle_query('vintage graphic tee under $30', 'Example wardrobe')
    print('=== GRADIO UI INTEGRATION ===\n')
    print('Test 1: Happy path')
    print(f'Listing panel output:\n{listing}\n')
    print(f'Outfit panel first 80 chars:\n{outfit[:80]}...\n')
    print(f'Fit card panel first 80 chars:\n{fit_card[:80]}...\n')

    # Test 2: Empty query
    listing2, outfit2, fit_card2 = handle_query('', 'Example wardrobe')
    print('Test 2: Empty query')
    print(f'Listing panel: {listing2}')
    print(f'Outfit panel: "{outfit2}"')
    print(f'Fit card panel: "{fit_card2}"')
    print()

    # Test 3: No results
    listing3, outfit3, fit_card3 = handle_query('designer ballgown size XXS under $5', 'Example wardrobe')
    print('Test 3: No results')
    print(f'Listing panel: {listing3}')
    print(f'Outfit panel: "{outfit3}"')
    print(f'Fit card panel: "{fit_card3}"')
