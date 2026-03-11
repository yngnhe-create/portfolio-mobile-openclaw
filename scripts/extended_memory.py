#!/usr/bin/env python3
"""
Extended Semantic Memory Search
Natural language Q&A, auto-tagging, and key information extraction
"""
import os
import re
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import json

class ExtendedSemanticMemory:
    def __init__(self, memory_dir="/Users/geon/.openclaw/workspace/memory"):
        self.memory_dir = memory_dir
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB (compatible version)
        self.client = chromadb.Client()
        
        self.collection = self.client.get_or_create_collection(
            name="memory_extended",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Auto-tagging patterns
        self.tag_patterns = {
            'earnings': ['실적', 'earnings', 'EPS', 'revenue', '매출', '영업이익'],
            'dividend': ['배당', 'dividend', '배당률', '배당금'],
            'policy': ['정책', 'policy', '금리', 'FOMC', '환율'],
            'risk': ['리스크', 'risk', '손절', '하락', '폭락'],
            'opportunity': ['기회', 'opportunity', '상승', '돌파', '신고가'],
            'stock': ['종목', 'stock', '티커', '코드'],
            'sector': ['섹터', 'sector', '업종', '산업'],
            'market': ['시장', 'market', '코스피', '코스닥', '나스닥']
        }
        
        self.indexed = False
    
    def extract_key_info(self, text):
        """Extract key information from text"""
        info = {
            'dates': [],
            'stocks': [],
            'prices': [],
            'percentages': [],
            'tags': []
        }
        
        # Extract dates
        date_patterns = [
            r'\d{4}[-/년]\s*\d{1,2}[-/월]\s*\d{1,2}[일]?',
            r'\d{1,2}월\s*\d{1,2}일',
            r'Q[1-4]\s*\d{4}',
            r'\d{4}년'
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            info['dates'].extend(matches)
        
        # Extract stock tickers (Korean format)
        stock_patterns = [
            r'([가-힣A-Za-z]+)\s*\(?\s*(\d{6})\s*\)?',
            r'(\d{6})\s*-?\s*([가-힣A-Za-z]+)'
        ]
        for pattern in stock_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    info['stocks'].append(f"{match[0]}({match[1]})")
        
        # Extract prices
        price_pattern = r'[\$₩]\s*[,\d]+(?:\.\d+)?(?:\s*원)?'
        info['prices'] = re.findall(price_pattern, text)
        
        # Extract percentages
        pct_pattern = r'[+-]?\d+\.?\d*\s*%'
        info['percentages'] = re.findall(pct_pattern, text)
        
        # Auto-tagging
        for tag, keywords in self.tag_patterns.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    info['tags'].append(tag)
                    break
        
        info['tags'] = list(set(info['tags']))
        return info
    
    def index_memories_with_metadata(self):
        """Index all memories with extracted metadata"""
        print("🔄 Indexing memories with metadata extraction...")
        
        import glob
        memory_files = glob.glob(os.path.join(self.memory_dir, "*.md"))
        
        documents = []
        metadatas = []
        ids = []
        
        for file_path in memory_files:
            file_name = os.path.basename(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            key_info = self.extract_key_info(content)
            
            # Chunk text
            chunks = self.chunk_text(content)
            
            for i, chunk in enumerate(chunks):
                chunk_info = self.extract_key_info(chunk)
                
                documents.append(chunk)
                metadatas.append({
                    "file": file_name,
                    "chunk": i,
                    "path": file_path,
                    "dates": json.dumps(chunk_info['dates'][:5]),
                    "stocks": json.dumps(chunk_info['stocks'][:5]),
                    "tags": json.dumps(chunk_info['tags']),
                    "last_modified": os.stat(file_path).st_mtime
                })
                ids.append(f"{file_name}_chunk_{i}")
        
        if documents:
            self.collection.delete(where={})
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            self.indexed = True
            print(f"✅ Indexed {len(documents)} chunks with metadata")
        
        return len(documents)
    
    def chunk_text(self, text, chunk_size=500, overlap=100):
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        return chunks
    
    def natural_language_query(self, query):
        """Process natural language queries"""
        # Query patterns and their interpretations
        query_patterns = {
            r'(?:이번 주|최근|요즘).*(?:수익|상승|오른).*(?:종목)?': self._get_recent_gainers,
            r'(?:이번 주|최근|요즘).*(?:하띭|손실|내린).*(?:종목)?': self._get_recent_losers,
            r'(?:배당|배당금|배당률).*?(?:높은|많은|좋은)?': self._get_dividend_info,
            r'(?:실적|earnings).*(?:발표|공시|나온)?': self._get_earnings_info,
            r'(?:손절|리스크|주의).*(?:필요|대상|종목)?': self._get_risk_alerts,
            r'(?:추천|관심|매수).*(?:종목|주식)?': self._get_recommendations,
            r'(?:시장|코스피|코스닥|나스닥).*(?:전망|흐름|상황)?': self._get_market_outlook,
        }
        
        for pattern, handler in query_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                return handler(query)
        
        # Default to semantic search
        return self._semantic_search(query)
    
    def _get_recent_gainers(self, query):
        """Query for recent gainers"""
        results = self.collection.query(
            query_texts=["수익률 상승 종목 top 수익"],
            n_results=10,
            where={"tags": {"$contains": "opportunity"}}
        )
        return self._format_nl_result("최근 수익률이 좋은 종목", results)
    
    def _get_recent_losers(self, query):
        """Query for recent losers"""
        results = self.collection.query(
            query_texts=["손실 하락 종목 리스크"],
            n_results=10,
            where={"tags": {"$contains": "risk"}}
        )
        return self._format_nl_result("최근 하락한 종목", results)
    
    def _get_dividend_info(self, query):
        """Query for dividend information"""
        results = self.collection.query(
            query_texts=["배당금 배당률 고배당"],
            n_results=10,
            where={"tags": {"$contains": "dividend"}}
        )
        return self._format_nl_result("배당 관련 정보", results)
    
    def _get_earnings_info(self, query):
        """Query for earnings information"""
        results = self.collection.query(
            query_texts=["실적 발표 EPS 매출"],
            n_results=10,
            where={"tags": {"$contains": "earnings"}}
        )
        return self._format_nl_result("실적 발표 정보", results)
    
    def _get_risk_alerts(self, query):
        """Query for risk alerts"""
        results = self.collection.query(
            query_texts=["손절 리스크 하락 주의"],
            n_results=10,
            where={"tags": {"$contains": "risk"}}
        )
        return self._format_nl_result("리스크 알림", results)
    
    def _get_recommendations(self, query):
        """Query for recommendations"""
        results = self.collection.query(
            query_texts=["매수 추천 관심 종목"],
            n_results=10,
            where={"tags": {"$contains": "opportunity"}}
        )
        return self._format_nl_result("추천 종목", results)
    
    def _get_market_outlook(self, query):
        """Query for market outlook"""
        results = self.collection.query(
            query_texts=["시장 전망 코스피 나스닥 흐름"],
            n_results=10,
            where={"tags": {"$contains": "market"}}
        )
        return self._format_nl_result("시장 전망", results)
    
    def _semantic_search(self, query):
        """Default semantic search"""
        results = self.collection.query(
            query_texts=[query],
            n_results=5
        )
        return self._format_nl_result(f"'{query}' 검색 결과", results)
    
    def _format_nl_result(self, title, results):
        """Format natural language results"""
        formatted = {
            'title': title,
            'results': [],
            'key_info': {
                'dates': [],
                'stocks': [],
                'tags': set()
            }
        }
        
        for doc, metadata, distance in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            relevance = (1 - distance) * 100
            
            # Parse metadata
            tags = json.loads(metadata.get('tags', '[]'))
            dates = json.loads(metadata.get('dates', '[]'))
            stocks = json.loads(metadata.get('stocks', '[]'))
            
            formatted['results'].append({
                'content': doc[:400] + "..." if len(doc) > 400 else doc,
                'file': metadata['file'],
                'relevance': f"{relevance:.1f}%",
                'tags': tags,
                'dates': dates[:3],
                'stocks': stocks[:3]
            })
            
            # Aggregate key info
            formatted['key_info']['dates'].extend(dates)
            formatted['key_info']['stocks'].extend(stocks)
            formatted['key_info']['tags'].update(tags)
        
        # Remove duplicates
        formatted['key_info']['dates'] = list(set(formatted['key_info']['dates']))[:5]
        formatted['key_info']['stocks'] = list(set(formatted['key_info']['stocks']))[:5]
        formatted['key_info']['tags'] = list(formatted['key_info']['tags'])
        
        return formatted
    
    def get_daily_digest(self):
        """Generate daily digest of important information"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Search for recent important info
        results = self.collection.query(
            query_texts=["중요 실적 발표 공시 알림", "시장 이벤트", "긴급"],
            n_results=10
        )
        
        digest = {
            'date': today,
            'important_events': [],
            'earnings': [],
            'alerts': [],
            'recommendations': []
        }
        
        for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
            tags = json.loads(metadata.get('tags', '[]'))
            
            if 'earnings' in tags:
                digest['earnings'].append(doc[:200])
            elif 'risk' in tags:
                digest['alerts'].append(doc[:200])
            elif 'opportunity' in tags:
                digest['recommendations'].append(doc[:200])
            else:
                digest['important_events'].append(doc[:200])
        
        return digest

def main():
    """CLI interface with extended features"""
    import sys
    
    memory = ExtendedSemanticMemory()
    
    if len(sys.argv) > 1 and sys.argv[1] == "index":
        memory.index_memories_with_metadata()
    
    elif len(sys.argv) > 1 and sys.argv[1] == "digest":
        digest = memory.get_daily_digest()
        print(f"\n📰 Daily Digest - {digest['date']}\n")
        print("=" * 60)
        
        print("\n🔔 Important Alerts:")
        for alert in digest['alerts'][:3]:
            print(f"  • {alert}")
        
        print("\n📊 Earnings:")
        for earning in digest['earnings'][:3]:
            print(f"  • {earning}")
        
        print("\n💡 Recommendations:")
        for rec in digest['recommendations'][:3]:
            print(f"  • {rec}")
    
    elif len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        result = memory.natural_language_query(query)
        
        print(f"\n🔍 {result['title']}\n")
        print("=" * 60)
        
        # Show key info
        if result['key_info']['tags']:
            print(f"\n🏷️  Tags: {', '.join(result['key_info']['tags'])}")
        if result['key_info']['stocks']:
            print(f"📈 Stocks: {', '.join(result['key_info']['stocks'])}")
        if result['key_info']['dates']:
            print(f"📅 Dates: {', '.join(result['key_info']['dates'])}")
        
        print("\n📋 Results:\n")
        for i, r in enumerate(result['results'], 1):
            print(f"{i}. [{r['relevance']}] {r['file']}")
            if r['tags']:
                print(f"   Tags: {', '.join(r['tags'])}")
            print(f"   {r['content'][:300]}...")
            print()
    
    else:
        print("Extended Semantic Memory Search")
        print("\nUsage:")
        print("  python3 extended_memory.py index")
        print("  python3 extended_memory.py digest")
        print("  python3 extended_memory.py <natural language query>")
        print("\nExamples:")
        print('  python3 extended_memory.py "이번 주 수익률 좋은 종목"')
        print('  python3 extended_memory.py "배당률 높은 종목 추천"')
        print('  python3 extended_memory.py "손절 필요한 종목 알려줘"')

if __name__ == "__main__":
    main()
