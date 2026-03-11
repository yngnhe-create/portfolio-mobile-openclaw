# 🤖 Discord Bot 연동 가이드

## 1. Discord Bot 생성

### Discord Developer Portal:
1. https://discord.com/developers/applications 접속
2. "New Application" 클릭
3. 이름: "PortfolioBot"
4. "Bot" 탭 → "Add Bot"
5. "Reset Token" → 토큰 복사

### 권한 설정:
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Add Reactions

### OAuth2 URL 생성:
```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=67584&scope=bot
```

## 2. Python Bot 코드

```python
import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot logged in as {bot.user}')
    # 자동 리포트 스케줄 시작
    daily_report.start()

@bot.command()
async def portfolio(ctx):
    """포트폴리오 현황 조회"""
    embed = discord.Embed(
        title="📊 포트폴리오 현황",
        description=f"{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        color=0x3498db
    )
    embed.add_field(name="💰 총 자산", value="₩11.4억", inline=True)
    embed.add_field(name="📈 YTD 수익률", value="+11.2%", inline=True)
    embed.add_field(name="📉 리스크 점수", value="68/100", inline=True)
    embed.add_field(
        name="🏆 TOP 3 수익 종목",
        value="1. 삼성전자 (+77.4M)\n2. 현대차3우B (+23.5M)\n3. 삼성전자우 (+21.2M)",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def wisereport(ctx):
    """와이즈리포트 조회"""
    embed = discord.Embed(
        title="📈 와이즈리포트 인사이트",
        color=0x2ecc71
    )
    embed.add_field(name="📊 전체 리포트", value="74개", inline=True)
    embed.add_field(name="💚 BUY 권장", value="44개", inline=True)
    embed.add_field(name="🎯 목표가 변경", value="27개", inline=True)
    embed.add_field(
        name="⭐ Today Best",
        value="디앤씨미디어 (매수, 목표가 17,000)",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def alert(ctx, stock: str, price: float):
    """알림 설정"""
    # TODO: DB에 알림 저장
    await ctx.send(f"✅ {stock} ₩{price:,} 알림 설정 완료!")

@bot.command()
async def action(ctx):
    ""️"오늘의 권장 액션"""
    actions = [
        "🔴 [즉시] 가상자산 비중 축소 (8.3% → 5%)",
        "🟢 [기회] 삼성SDI 추가 매수 (+34% 상승여력)",
        "🟢 [기회] 기아 추가 매수 (역사적 신고가)",
        "🔴 [즉시] 리츠 섹터 손절 검토 (-13.8%)",
    ]
    
    embed = discord.Embed(
        title="⚡ 오늘의 권장 액션",
        color=0xe74c3c
    )
    for action in actions:
        embed.add_field(name="\u200b", value=action, inline=False)
    
    await ctx.send(embed=embed)

@tasks.loop(hours=24)
async def daily_report():
    """매일 아침 8시 자동 리포트"""
    channel = bot.get_channel(CHANNEL_ID)  # #리포트 채널 ID
    
    if channel:
        embed = discord.Embed(
            title="📊 아침 투자 리포트",
            description=f"{datetime.now().strftime('%Y년 %m월 %d일')}",
            color=0x9b59b6
        )
        
        # Content Factory에서 생성된 데이터
        embed.add_field(name="💰 총 자산", value="₩11.4억", inline=True)
        embed.add_field(name="📈 YTD", value="+11.2%", inline=True)
        embed.add_field(name="⚠️ 리스크", value="중간 (68점)", inline=True)
        
        await channel.send(embed=embed)

@daily_report.before_loop
async def before_daily_report():
    await bot.wait_until_ready()
    # 8시까지 대기
    now = datetime.now()
    target = now.replace(hour=8, minute=0, second=0)
    if now > target:
        target = target.replace(day=target.day + 1)
    await discord.utils.sleep_until(target)

# 실행
BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
bot.run(BOT_TOKEN)
```

## 3. 슬래시 커맨드 (Slash Commands)

```python
from discord import app_commands

@bot.tree.command(name="portfolio", description="포트폴리오 현황 조회")
async def slash_portfolio(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 포트폴리오",
        color=0x3498db
    )
    embed.add_field(name="총 자산", value="₩11.4억")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stock", description="특정 종목 조회")
@app_commands.describe(stock="종목명 또는 티커")
async def slash_stock(interaction: discord.Interaction, stock: str):
    # 종목 데이터 조회
    data = get_stock_data(stock)
    
    embed = discord.Embed(
        title=f"📈 {stock}",
        color=0x2ecc71 if data['pnl'] > 0 else 0xe74c3c
    )
    embed.add_field(name="현재가", value=data['price'])
    embed.add_field(name="손익", value=f"{data['pnl']:+}%")
    
    await interaction.response.send_message(embed=embed)

# 슬래시 커맨드 동기화
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("✅ Slash commands synced")
```

## 4. Content Factory 통합

```python
# content_factory_discord.py

import discord
import asyncio
from datetime import datetime

class ContentFactoryDiscord:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.bot = None
        
    async def send_research(self, channel_id, data):
        """리서치 결과 전송"""
        channel = self.bot.get_channel(channel_id)
        
        embed = discord.Embed(
            title="🔍 시장 리서치",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        for key, value in data.items():
            embed.add_field(name=key, value=value, inline=True)
        
        await channel.send(embed=embed)
    
    async def send_report(self, channel_id, report_md):
        """리포트 전송"""
        channel = self.bot.get_channel(channel_id)
        
        # 파일로 첨부
        with open('report.md', 'w') as f:
            f.write(report_md)
        
        await channel.send(
            "📄 투자 리포트",
            file=discord.File('report.md')
        )
    
    async def send_alert(self, channel_id, stock, action):
        """알림 전송"""
        channel = self.bot.get_channel(channel_id)
        
        color = 0x2ecc71 if action == 'buy' else 0xe74c3c
        emoji = "🟢" if action == 'buy' else "🔴"
        
        await channel.send(
            f"{emoji} **{stock}** 알림: {action.upper()} 신호"
        )

# 사용
async def main():
    factory = ContentFactoryDiscord(BOT_TOKEN)
    
    # 각 채널에 전송
    await factory.send_research(CHANNEL_RESEARCH, research_data)
    await factory.send_report(CHANNEL_REPORT, report_content)
    await factory.send_alert(CHANNEL_ALERT, "삼성전자", "buy")

asyncio.run(main())
```

## 장점/단점

✅ **장점:**
- 양방향 통신 (명령어 응답)
- 실시간 상호작용
- 복잡한 로직 구현 가능
- 데이터베이스 연동 가능

❌ **단점:**
- 서버 24시간 실행 필요 (또는 클라우드)
- 설정 복잡
- 물리적 비용 발생 가능 (큐브호스팅 등)

## 호스팅 옵션

| 옵션 | 비용 | 난이도 |
|:---|---:|:---|
| 로컬 PC | ₩0 | 쉬움 (24시간 켜두기) |
| Raspberry Pi | ₩5만(일회성) | 중간 |
| AWS EC2 | 월 ₩10~20 | 중간 |
| Heroku | 물료~월 $7 | 쉬움 |
| Oracle Cloud | 물료 | 중간 |
