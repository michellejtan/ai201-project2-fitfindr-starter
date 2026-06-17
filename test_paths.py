from agent import run_agent
from utils.data_loader import get_example_wardrobe

if __name__ == "__main__":
    # Test 1: Happy path
    session = run_agent(
        query='vintage graphic tee under $30',
        wardrobe=get_example_wardrobe(),
    )

    print('=== STATE FLOW VERIFICATION ===\n')
    print('Test 1: Happy path')
    selected_item = session.get('selected_item')
    print('1. selected_item type: {}'.format(type(selected_item)))
    print('   selected_item keys: {}'.format(list(selected_item.keys()) if selected_item else 'None'))
    print('   selected_item id: {}'.format(selected_item.get('id') if selected_item else 'N/A'))
    print()
    print('2. outfit_suggestion first 100 chars: {}'.format(session.get('outfit_suggestion', '')[:100] or 'None'))
    print()
    print('3. fit_card first 100 chars: {}'.format(session.get('fit_card', '')[:100] or 'None'))
    print()
    print('4. error: {}'.format(session.get('error')))
    print()

    # Verify state dependency: outfit_suggestion should reference the selected_item in some way
    print('=== Branching Test ===\n')
    session2 = run_agent(
        query='designer ballgown size XXS under $5',
        wardrobe=get_example_wardrobe(),
    )
    print('No-results path:')
    print(f"  search_results: {session2['search_results']}")
    print(f"  selected_item: {session2['selected_item']}")
    print(f"  outfit_suggestion: {session2['outfit_suggestion']}")
    print(f"  fit_card: {session2['fit_card']}")
    print(f"  error: {session2['error']}")
