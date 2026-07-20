"""Entry point for python3 -m src"""
import sys
import traceback

try:
    from src.cli import main
    main()
except KeyboardInterrupt:
    print("\nGoodbye!")
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)
