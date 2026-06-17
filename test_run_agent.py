from agent import run_agent
from utils.data_loader import get_example_wardrobe

if __name__ == "__main__":
    session = run_agent(
        query='vintage graphic tee size M under $30',
        wardrobe=get_example_wardrobe(),
    )

    print('Query with explicit size:')
    print('  Input: "vintage graphic tee size M under $30"')
    print(f"  Parsed description: \"{session['parsed']['description']}\"")
    print(f"  Parsed size: {session['parsed']['size']}")
    print(f"  Parsed max_price: {session['parsed']['max_price']}")
    print()
    print(f"  Selected item title: {session['selected_item']['title']}")
    print(f"  Selected item size: {session['selected_item']['size']}")
    print(f"  Selected item price: {session['selected_item']['price']}")
