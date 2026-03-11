#!/usr/bin/env python3
"""
Extended Memory Search - Simple Version (No ChromaDB)
Natural language Q&A with regex-based search
"""
import os
import re
import glob
import json
from datetime import datetime, timedelta
from collections import Counter

class SimpleMemorySearch:
    def __init__(self, memory_dir="/Users/geon/.openclaw/workspace/memory"):
        self.memory_dir = memory_dir
        self.memories = []
        self.indexed = False
        
        # Auto-tagging keywords
        self.tag_keywords = {
            'earnings': ['실적', 'earnings', 'EPS', '매출', '영업이익', '순이익'],
            'dividend': ['배당', 'dividend', '배당률', '배당금', '배당수익률'],
            'policy': ['정책', 'policy', '금리', 'FOMC', 'CPI', 'PPI', '환율'],
            'risk': ['리스크', 'risk', '손절', '하락', '폭락', '주의', '경고'],
            'opportunity': ['기회', 'opportunity', '상승', '돌파', '신고가', '추천'],
            'market': ['시장', 'market', '코스피', '코스닥', '나스닥', '다우']
        }
    
    def load_memories(self):
        """Load all memory files"""
        print("🔄 Loading memory files...")
        
        memory_files = glob.glob(os.path.join(self.memory_dir, "*.md"))
        
        for file_path in memory_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            info = self.extract_info(content)
            
            self.memories.append({
                'file': os.path.basename(file_path),
                'content': content,
                'chunks': self.chunk_text(content),
                'info': info
            })
        
        self.indexed = True
        print(f"✅ Loaded {len(self.memories)} files")
    
    def chunk_text(self, text, chunk_size=800):
        """Split text into chunks"""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            if current_size + len(line) > chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = len(line)
            else:
                current_chunk.append(line)
                current_size += len(line)
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def extract_info(self, text):
        """Extract key information"""
        info = {
            'dates': [],
            'stocks': [],
            'prices': [],
            'percentages': [],
            'tags': []
        }
        
        # Dates
        date_patterns = [
            r'\d{4}[-/년]\s*\d{1,2}[-/월]\s*\d{1,2}[일]?',
            r'\d{1,2}월\s*\d{1,2}일',
            r'Q[1-4]\s*\d{4}'
        ]
        for pattern in date_patterns:
            info['dates'].extend(re.findall(pattern, text))
        
        # Stock names (Korean)
        stock_pattern = r'([가-힣A-Za-z]{2,20})\s*\(?\s*(?:005930|000660|035420|006400|373220|051910|003670|009830|031980|214450|357250|245340|051910)'
        matches = re.findall(stock_pattern, text)
        info['stocks'] = list(set(matches))
        
        # Prices
        info['prices'] = re.findall(r'[\$₩]\s*[\d,]+(?:\.\d+)?', text)[:10]
        
        # Percentages
        info['percentages'] = re.findall(r'[+-]?\d+\.?\d*\s*%', text)[:10]
        
        # Auto-tagging
        for tag, keywords in self.tag_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    info['tags'].append(tag)
                    break
        
        info['tags'] = list(set(info['tags']))
        return info
    
    def search(self, query, top_k=5):
        """Search memories with scoring"""
        if not self.indexed:
            self.load_memories()
        
        # Parse query intent
        query_lower = query.lower()
        intent_tags = []
        
        if any(w in query_lower for w in ['수익', '상승', '오른', '추천']):
            intent_tags.append('opportunity')
        if any(w in query_lower for w in ['손실', '하띭', '내린', '손절']):
            intent_tags.append('risk')
        if any(w in query_lower for w in ['배당', '배당금']):
            intent_tags.append('dividend')
        if any(w in query_lower for w in ['실적', 'earnings']):
            intent_tags.append('earnings')
        
        results = []
        
        for memory in self.memories:
            for i, chunk in enumerate(memory['chunks']):
                score = 0
                
                # Keyword matching
                query_words = set(query_lower.split())
                chunk_words = set(chunk.lower().split())
                overlap = len(query_words & chunk_words)
                score += overlap * 10
                
                # Tag matching
                for tag in intent_tags:
                    if tag in memory['info']['tags']:
                        score += 20
                
                # Recent files bonus
                if '2026-03' in memory['file'] or '2026-02' in memory['file']:
                    score += 5
                
                if score > 0:
                    results.append({
                        'file': memory['file'],
                        'chunk': chunk[:500],
                        'score': score,
                        'tags': memory['info']['tags'],
                        'dates': memory['info']['dates'][:3],
                        'stocks': memory['info']['stocks'][:5]
                    })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def get_daily_summary(self):
        """Generate daily summary"""
        if not self.indexed:
            self.load_memories()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Collect all tags
        all_tags = []
        all_stocks = []
        recent_contents = []
        
        for memory in self.memories:
            # Recent files only
            if '2026-03' in memory['file'] or '2026-02-27' in memory['file']:
                all_tags.extend(memory['info']['tags'])
                all_stocks.extend(memory['info']['stocks'])
                recent_contents.append(memory['content'][:1000])
        
        # Count tag frequency
        tag_counts = Counter(all_tags)
        stock_counts = Counter(all_stocks)
        
        return {
            'date': today,
            'top_tags': tag_counts.most_common(5),
            'mentioned_stocks': stock_counts.most_common(10),
            'recent_updates': len(recent_contents)
        }

def main():
    import sys
    
    search = SimpleMemorySearch()
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        results = search.search(query)
        
        print(f"\n🔍 검색: '{query}'\n")
        print("=" * 60)
        
        for i, r in enumerate(results, 1):
            print(f"\n{i}. 📄 {r['file']} (Score: {r['score']})")
            if r['tags']:
                print(f"   🏷️  {', '.join(r['tags'])}")
            if r['stocks']:
                print(f"   📈 종목: {', '.join(r['stocks'])}")
            print(f"   {r['chunk'][:400]}...")
    else:
        # Daily summary
        summary = search.get_daily_summary()
        print(f"\n📰 Daily Summary - {summary['date']}\n")
        print("=" * 60)
        print(f"\n최근 업데이트: {summary['recent_updates']}개 파일")
        
        print("\n🔥 주요 태그:")
        for tag, count in summary['top_tags']:
            print(f"  • {tag}: {count}회")
        
        print("\n📊 언급된 종목:")
        for stock, count in summary['mentioned_stocks']:
            print(f"  • {stock}: {count}회")

if __name__ == "__main__":
    main()
