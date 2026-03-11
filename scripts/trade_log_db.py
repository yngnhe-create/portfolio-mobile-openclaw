#!/usr/bin/env python3
"""
Database-based Trade Log System
SQLite database for trade pattern analysis and tax reporting
"""
import sqlite3
import pandas as pd
from datetime import datetime
import os

class TradeLogDatabase:
    def __init__(self, db_path="/Users/geon/.openclaw/workspace/trade_logs.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables"""
        # Trades table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset TEXT NOT NULL,
                ticker TEXT,
                sector TEXT,
                trade_type TEXT CHECK(trade_type IN ('BUY', 'SELL')),
                quantity REAL,
                price REAL,
                amount REAL,
                currency TEXT DEFAULT 'KRW',
                trade_date DATE,
                strategy TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Portfolio snapshots table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date DATE,
                total_value REAL,
                total_pnl REAL,
                cash_balance REAL,
                num_positions INTEGER,
                top_sector TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Strategy performance table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT,
                period_start DATE,
                period_end DATE,
                total_return REAL,
                num_trades INTEGER,
                win_rate REAL,
                avg_pnl REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def import_from_csv(self, csv_path="/Users/geon/.openclaw/workspace/portfolio_full.csv"):
        """Import current portfolio from CSV"""
        df = pd.read_csv(csv_path)
        
        print(f"📊 Importing {len(df)} positions from CSV...")
        
        for _, row in df.iterrows():
            # Parse values
            asset = row['자산']
            sector = row['분류']
            qty = row['수량']
            
            # Parse current price
            price_str = str(row['현재가'])
            if '₩' in price_str:
                price = float(price_str.replace('₩', '').replace(',', ''))
                currency = 'KRW'
            elif '$' in price_str:
                price = float(price_str.replace('$', '').replace(',', ''))
                currency = 'USD'
            else:
                price = 0
                currency = 'KRW'
            
            # Calculate amount
            amount = qty * price
            
            # Insert as current position
            self.cursor.execute('''
                INSERT INTO trades (asset, sector, trade_type, quantity, price, amount, currency, trade_date, strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (asset, sector, 'BUY', qty, price, amount, currency, datetime.now().strftime('%Y-%m-%d'), 'HOLDING'))
        
        self.conn.commit()
        print(f"✅ Imported {len(df)} positions")
    
    def add_trade(self, asset, ticker, sector, trade_type, quantity, price, currency='KRW', strategy='', notes=''):
        """Add a new trade"""
        amount = quantity * price
        trade_date = datetime.now().strftime('%Y-%m-%d')
        
        self.cursor.execute('''
            INSERT INTO trades (asset, ticker, sector, trade_type, quantity, price, amount, currency, trade_date, strategy, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (asset, ticker, sector, trade_type, quantity, price, amount, currency, trade_date, strategy, notes))
        
        self.conn.commit()
        print(f"✅ Added {trade_type} trade: {asset} x{quantity} @ {price}")
    
    def get_trade_summary(self, period='YTD'):
        """Get trade summary for a period"""
        if period == 'YTD':
            start_date = f"{datetime.now().year}-01-01"
        elif period == 'Q1':
            start_date = f"{datetime.now().year}-01-01"
        elif period == 'Q2':
            start_date = f"{datetime.now().year}-04-01"
        elif period == 'Q3':
            start_date = f"{datetime.now().year}-07-01"
        elif period == 'Q4':
            start_date = f"{datetime.now().year}-10-01"
        else:
            start_date = '2000-01-01'
        
        # Get trades by sector
        self.cursor.execute('''
            SELECT sector, COUNT(*) as trades, SUM(CASE WHEN trade_type='SELL' THEN amount ELSE 0 END) as sells
            FROM trades
            WHERE trade_date >= ?
            GROUP BY sector
            ORDER BY trades DESC
        ''', (start_date,))
        
        sector_summary = self.cursor.fetchall()
        
        # Get trades by strategy
        self.cursor.execute('''
            SELECT strategy, COUNT(*) as trades, AVG(amount) as avg_amount
            FROM trades
            WHERE trade_date >= ? AND strategy != ''
            GROUP BY strategy
            ORDER BY trades DESC
        ''', (start_date,))
        
        strategy_summary = self.cursor.fetchall()
        
        return {
            'period': period,
            'sector_summary': sector_summary,
            'strategy_summary': strategy_summary
        }
    
    def get_tax_report(self, year=None):
        """Generate tax report for a year"""
        if year is None:
            year = datetime.now().year
        
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        self.cursor.execute('''
            SELECT 
                asset,
                SUM(CASE WHEN trade_type='BUY' THEN amount ELSE 0 END) as total_buy,
                SUM(CASE WHEN trade_type='SELL' THEN amount ELSE 0 END) as total_sell,
                COUNT(*) as num_trades
            FROM trades
            WHERE trade_date BETWEEN ? AND ?
            GROUP BY asset
            ORDER BY num_trades DESC
        ''', (start_date, end_date))
        
        return self.cursor.fetchall()
    
    def get_best_worst_performers(self, limit=5):
        """Get best and worst performing trades"""
        # This would require tracking realized P&L
        # For now, return most traded assets
        self.cursor.execute('''
            SELECT asset, sector, COUNT(*) as trades, SUM(amount) as total_volume
            FROM trades
            GROUP BY asset
            ORDER BY total_volume DESC
            LIMIT ?
        ''', (limit,))
        
        return self.cursor.fetchall()
    
    def close(self):
        """Close database connection"""
        self.conn.close()

def main():
    """CLI interface"""
    import sys
    
    db = TradeLogDatabase()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "import":
            db.import_from_csv()
        
        elif command == "summary":
            period = sys.argv[2] if len(sys.argv) > 2 else 'YTD'
            results = db.get_trade_summary(period)
            
            print(f"\n📊 Trade Summary ({results['period']})\n")
            print("=" * 60)
            
            print("\nBy Sector:")
            for sector, trades, sells in results['sector_summary']:
                print(f"  {sector}: {trades} trades")
            
            print("\nBy Strategy:")
            for strategy, trades, avg_amount in results['strategy_summary']:
                print(f"  {strategy}: {trades} trades (avg ₩{avg_amount:,.0f})")
        
        elif command == "tax":
            year = int(sys.argv[2]) if len(sys.argv) > 2 else datetime.now().year
            results = db.get_tax_report(year)
            
            print(f"\n📋 Tax Report for {year}\n")
            print("=" * 60)
            print(f"{'Asset':<20} {'Total Buy':<15} {'Total Sell':<15} {'Trades':<10}")
            print("-" * 60)
            
            for asset, total_buy, total_sell, num_trades in results:
                print(f"{asset:<20} ₩{total_buy:<14,.0f} ₩{total_sell:<14,.0f} {num_trades:<10}")
        
        elif command == "top":
            results = db.get_best_worst_performers()
            
            print("\n🏆 Top Traded Assets\n")
            print("=" * 60)
            print(f"{'Rank':<6} {'Asset':<20} {'Sector':<15} {'Trades':<10} {'Volume':<15}")
            print("-" * 60)
            
            for i, (asset, sector, trades, volume) in enumerate(results, 1):
                print(f"{i:<6} {asset:<20} {sector:<15} {trades:<10} ₩{volume:,.0f}")
        
        else:
            print("Commands:")
            print("  import              - Import from CSV")
            print("  summary [period]    - Trade summary (YTD, Q1, Q2, Q3, Q4)")
            print("  tax [year]          - Tax report for year")
            print("  top                 - Top traded assets")
    else:
        # Import by default
        db.import_from_csv()
    
    db.close()

if __name__ == "__main__":
    main()
