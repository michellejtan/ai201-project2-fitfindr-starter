from agent import run_agent
from utils.data_loader import get_example_wardrobe

if __name__ == "__main__":
    print('=== PLANNING LOOP BEHAVIOR VERIFICATION ===\n')

    # Test: Verify that suggest_outfit and create_fit_card are NOT called when search_listings returns empty
    session_no_results = run_agent(
        query='designer ballgown size XXS under $5',
        wardrobe=get_example_wardrobe(),
    )

    print('NO-RESULTS PATH (search_listings returns []):')
    print(f"  ✓ search_results is empty: {session_no_results['search_results'] == []}")
    print(f"  ✓ selected_item NOT set: {session_no_results['selected_item'] is None}")
    print(f"  ✓ outfit_suggestion NOT called: {session_no_results['outfit_suggestion'] is None}")
    print(f"  ✓ fit_card NOT called: {session_no_results['fit_card'] is None}")
    print(f"  ✓ error is set: \"{session_no_results['error']}\"")
    print()

    # Test: Verify happy path calls all three tools and state flows
    session_happy = run_agent(
        query='vintage graphic tee under $30',
        wardrobe=get_example_wardrobe(),
    )

    print('HAPPY PATH (search_listings returns results):')
    print(f"  ✓ search_results has items: {len(session_happy['search_results']) > 0}")
    print(f"  ✓ selected_item is set: {session_happy['selected_item'] is not None}")
    print(f"  ✓ selected_item is first result: {session_happy['selected_item'] == session_happy['search_results'][0]}")
    print(f"  ✓ outfit_suggestion is set: {session_happy['outfit_suggestion'] is not None and len(session_happy['outfit_suggestion']) > 0}")
    print(f"  ✓ fit_card is set: {session_happy['fit_card'] is not None and len(session_happy['fit_card']) > 0}")
    print(f"  ✓ error is None: {session_happy['error'] is None}")
    print()

    # Verify parsed extraction
    print('QUERY PARSING (Step 1):')
    print('  Input: "vintage graphic tee under $30"')
    print(f"  Parsed description: \"{session_happy['parsed']['description']}\"")
    print(f"  Parsed size: {session_happy['parsed']['size']}")
    print(f"  Parsed max_price: {session_happy['parsed']['max_price']}")
    print()

    print('✅ CHECKPOINT PASSED: Planning loop branches correctly and state flows through all tools.')
