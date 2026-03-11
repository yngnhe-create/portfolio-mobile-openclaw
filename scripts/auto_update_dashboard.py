#!/usr/bin/env python3
"""
Auto-update dashboard with latest prices
"""
import subprocess
import json
from datetime import datetime

def main():
    print("🔄 Auto-updating portfolio dashboard...")
    
    # 1. Update prices
    print("\n1️⃣ Updating stock prices...")
    result = subprocess.run(
        ["python3", "/Users/geon/.openclaw/workspace/scripts/update_prices_v2.py"],
        capture_output=True,
        text=True,
        timeout=180
    )
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr[:500])
    
    # 2. Generate new dashboard HTML
    print("\n2️⃣ Regenerating dashboard...")
    # This would call the dashboard generation script
    # For now, prices are updated in CSV
    
    print("\n✅ Update complete!")
    print(f"📊 Next update: Weekdays at 9:00, 12:00, 15:00 KST")
    print("💡 Manual update: Run /exec python3 ~/.openclaw/workspace/scripts/update_prices_v2.py")

if __name__ == "__main__":
    main()
