#!/usr/bin/env python3
"""
Portfolio History Tracker
Tracks daily portfolio value and calculates returns
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta

WORKSPACE = "/Users/geon/.openclaw/workspace"
HISTORY_FILE = f"{WORKSPACE}/memory/portfolio_history.json"

def load_history():
    """Load portfolio history"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    """Save portfolio history"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def add_daily_snapshot(total_value, total_pnl, total_pnl_pct):
    """Add today's snapshot"""
    history = load_history()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Check if today already exists
    existing = [h for h in history if h['date'] == today]
    if existing:
        # Update today's entry
        existing[0]['value'] = total_value
        existing[0]['pnl'] = total_pnl
        existing[0]['pnl_pct'] = total_pnl_pct
    else:
        # Add new entry
        history.append({
            'date': today,
            'value': total_value,
            'pnl': total_pnl,
            'pnl_pct': total_pnl_pct,
            'timestamp': datetime.now().isoformat()
        })
    
    # Keep only last 365 days
    history = sorted(history, key=lambda x: x['date'])[-365:]
    
    save_history(history)
    return history

def get_ytd_return(history):
    """Calculate Year-To-Date return"""
    if not history:
        return None
    
    current_year = datetime.now().year
    year_start = f"{current_year}-01-01"
    
    # Find first entry of current year
    year_entries = [h for h in history if h['date'] >= year_start]
    if not year_entries:
        return None
    
    first_entry = min(year_entries, key=lambda x: x['date'])
    latest_entry = max(history, key=lambda x: x['date'])
    
    ytd_return = ((latest_entry['value'] - first_entry['value']) / first_entry['value']) * 100
    
    return {
        'start_date': first_entry['date'],
        'start_value': first_entry['value'],
        'current_value': latest_entry['value'],
        'return_pct': ytd_return
    }

def get_period_return(history, days):
    """Calculate return for specific period"""
    if not history or len(history) < 2:
        return None
    
    latest = max(history, key=lambda x: x['date'])
    latest_date = datetime.strptime(latest['date'], '%Y-%m-%d')
    
    target_date = latest_date - timedelta(days=days)
    target_date_str = target_date.strftime('%Y-%m-%d')
    
    # Find closest entry to target date
    past_entries = [h for h in history if h['date'] <= target_date_str]
    if not past_entries:
        return None
    
    past_entry = max(past_entries, key=lambda x: x['date'])
    
    return_pct = ((latest['value'] - past_entry['value']) / past_entry['value']) * 100
    
    return {
        'period': f"{days}일",
        'start_date': past_entry['date'],
        'start_value': past_entry['value'],
        'return_pct': return_pct
    }

def get_value_trend(history, days=7):
    """Get value trend for chart"""
    if not history:
        return []
    
    sorted_history = sorted(history, key=lambda x: x['date'])
    
    # Get last N days
    recent = sorted_history[-days:]
    
    return [
        {
            'date': h['date'][5:],  # MM-DD format
            'value': h['value'],
            'pnl_pct': h['pnl_pct']
        }
        for h in recent
    ]

if __name__ == "__main__":
    # Test
    history = load_history()
    print(f"History entries: {len(history)}")
    
    ytd = get_ytd_return(history)
    if ytd:
        print(f"\nYTD Return: {ytd['return_pct']:+.2f}%")
        print(f"  From: {ytd['start_date']} (₩{ytd['start_value']:,.0f})")
        print(f"  To:   ₩{ytd['current_value']:,.0f}")
    
    returns_7d = get_period_return(history, 7)
    if returns_7d:
        print(f"\n7-Day Return: {returns_7d['return_pct']:+.2f}%")
    
    returns_30d = get_period_return(history, 30)
    if returns_30d:
        print(f"30-Day Return: {returns_30d['return_pct']:+.2f}%")