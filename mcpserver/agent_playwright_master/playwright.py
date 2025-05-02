from playwright.async_api import Browser, Page, Playwright, async_playwright
from agents import Agent, AsyncComputer, Button, ComputerTool, Environment, ModelSettings, Runner
from config import PLAYWRIGHT_HEADLESS
import base64,asyncio,sys,re,json,time
from typing import Literal, Union, Optional, Any, Dict, List, Tuple
from dataclasses import dataclass, asdict
from .message_filter import filter_messages

print=lambda *a,**k:sys.stderr.write('[print] '+(' '.join(map(str,a)))+'\n')

# 键盘映射表
CUA_KEY_TO_PLAYWRIGHT_KEY = {
    "/": "Divide",
    "\\": "Backslash", 
    "alt": "Alt",
    "arrowdown": "ArrowDown",
    "arrowleft": "ArrowLeft",
    "arrowright": "ArrowRight", 
    "arrowup": "ArrowUp",
    "backspace": "Backspace",
    "capslock": "CapsLock",
    "cmd": "Meta",
    "ctrl": "Control",
    "delete": "Delete",
    "end": "End",
    "enter": "Enter",
    "esc": "Escape",
    "home": "Home",
    "insert": "Insert",
    "option": "Alt",
    "pagedown": "PageDown",
    "pageup": "PageUp",
    "shift": "Shift",
    "space": " ",
    "super": "Meta",
    "tab": "Tab",
    "win": "Meta",
}

@dataclass
class BrowserContext:
    """浏览器上下文"""
    url: str = ""
    page_title: str = ""
    page_content: str = ""
    history: List[Dict] = None
    
    def __post_init__(self):
        if self.history is None:
            self.history = []
            
    def update(self, url: str, title: str = "", content: str = ""):
        self.url = url
        self.page_title = title
        self.page_content = content
        self.history.append({
            "url": url,
            "title": title,
            "timestamp": time.time()
        })
        
    def to_dict(self) -> dict:
        return asdict(self)

class LocalPlaywrightComputer(AsyncComputer):
    """本地Playwright浏览器实现"""
    def __init__(self):
        self._playwright: Union[Playwright, None] = None
        self._browser: Union[Browser, None] = None
        self._page: Union[Page, None] = None
        self.context = BrowserContext()
        
    async def _get_browser_and_page(self) -> Tuple[Browser, Page]:
        """获取浏览器和页面实例"""
        width, height = self.dimensions
        launch_args = [
            f"--window-size={width},{height}",
            "--disable-gpu",
            "--no-sandbox"
        ]
        browser = await self.playwright.chromium.launch(
            headless=PLAYWRIGHT_HEADLESS,
            args=launch_args
        )
        page = await browser.new_page()
        await page.set_viewport_size({"width": width, "height": height})
        return browser, page

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._playwright = await async_playwright().start()
        self._browser, self._page = await self._get_browser_and_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    @property
    def playwright(self) -> Playwright:
        assert self._playwright is not None
        return self._playwright

    @property
    def browser(self) -> Browser:
        assert self._browser is not None
        return self._browser

    @property
    def page(self) -> Page:
        assert self._page is not None
        return self._page

    @property
    def environment(self) -> Environment:
        return "browser"

    @property
    def dimensions(self) -> Tuple[int, int]:
        return (1024, 768)

    async def screenshot(self) -> str:
        """截图"""
        png_bytes = await self.page.screenshot(full_page=False)
        return base64.b64encode(png_bytes).decode("utf-8")

    async def click(self, x: int, y: int, button: Button = "left") -> None:
        """点击"""
        playwright_button: Literal["left", "middle", "right"] = "left"
        if button in ("left", "right", "middle"):
            playwright_button = button # type: ignore
        await self.page.mouse.click(x, y, button=playwright_button)

    async def double_click(self, x: int, y: int) -> None:
        """双击"""
        await self.page.mouse.dblclick(x, y)

    async def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        """滚动"""
        await self.page.mouse.move(x, y)
        await self.page.evaluate(f"window.scrollBy({scroll_x}, {scroll_y})")

    async def type(self, text: str) -> None:
        """输入文本"""
        await self.page.keyboard.type(text)

    async def wait(self) -> None:
        """等待"""
        await asyncio.sleep(1)

    async def move(self, x: int, y: int) -> None:
        """移动鼠标"""
        await self.page.mouse.move(x, y)

    async def keypress(self, keys: List[str]) -> None:
        """按键"""
        mapped_keys = [CUA_KEY_TO_PLAYWRIGHT_KEY.get(key.lower(), key) for key in keys]
        for key in mapped_keys:
            await self.page.keyboard.down(key)
        for key in reversed(mapped_keys):
            await self.page.keyboard.up(key)

    async def drag(self, path: List[Tuple[int, int]]) -> None:
        """拖拽"""
        if not path:
            return
        await self.page.mouse.move(path[0][0], path[0][1])
        await self.page.mouse.down()
        for px, py in path[1:]:
            await self.page.mouse.move(px, py)
        await self.page.mouse.up()

    async def open_url(self, url: str) -> str:
        """打开URL并返回状态"""
        try:
            sys.stderr.write(f'正在打开URL: {url}\n')
            await self.page.goto(url, wait_until='networkidle')
            title = await self.page.title()
            content = await self.page.content()
            self.context.update(url=url, title=title, content=content)
            return 'ok'
        except Exception as e:
            sys.stderr.write(f'打开URL失败: {e}\n')
            return str(e)

class PlaywrightAgent(Agent):
    """Playwright浏览器代理"""
    def __init__(self):
        super().__init__(
            name="Playwright Browser Agent",
            instructions="You are a helpful browser automation agent.",
            tools=[ComputerTool(LocalPlaywrightComputer())],
            model="computer-use-preview",
            model_settings=ModelSettings(truncation="auto")
        )
        sys.stderr.write('PlaywrightAgent初始化完成\n')

    async def handle_handoff(self, data: dict) -> str:
        """处理handoff请求"""
        try:
            sys.stderr.write(f'收到handoff请求数据: {json.dumps(data, ensure_ascii=False)}\n')
            
            # 验证数据格式
            if not isinstance(data, dict):
                raise ValueError(f"无效的数据格式: {type(data)}")
            
            # 验证必需字段
            if "query" not in data:
                raise ValueError("缺少必需的query字段")
                
            # 提取URL
            url = data.get("url")
            if not url:
                url = extract_url(data["query"])
                
            if not url:
                return json.dumps({
                    'status': 'error',
                    'message': '无法识别网址',
                    'context': {}
                }, ensure_ascii=False)
            
            # 确保URL格式正确
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            # 打开URL
            sys.stderr.write(f'准备打开URL: {url}\n')
            async with LocalPlaywrightComputer() as computer:
                result = await computer.open_url(url)
                sys.stderr.write(f'open_url结果: {result}\n')
                
                response = {
                    'status': 'ok' if result == 'ok' else 'error',
                    'message': result if result != 'ok' else '',
                    'context': computer.context.to_dict()
                }
                
            sys.stderr.write(f'返回响应: {json.dumps(response, ensure_ascii=False)}\n')
            return json.dumps(response, ensure_ascii=False)
            
        except Exception as e:
            sys.stderr.write(f'handle_handoff异常: {e}\n')
            import traceback;traceback.print_exc(file=sys.stderr)
            return json.dumps({
                'status': 'error',
                'message': str(e),
                'context': {}
            }, ensure_ascii=False)

def extract_url(text: str) -> str:
    """从文本中提取URL"""
    if not text:
        return ""
        
    # 直接URL模式
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(url_pattern, text)
    if urls:
        url = urls[0]
        if not url.startswith('http'):
            url = 'https://' + url
        return url
    
    # 常见网站名称映射
    site_map = {
        'bilibili': 'https://www.bilibili.com',
        'b站': 'https://www.bilibili.com', 
        'youtube': 'https://www.youtube.com',
        'google': 'https://www.google.com',
        'baidu': 'https://www.baidu.com',
        '百度': 'https://www.baidu.com',
        'github': 'https://github.com',
    }
    
    # 检查是否包含已知网站名称
    for site, url in site_map.items():
        if site.lower() in text.lower():
            return url
            
    return ""

if __name__=="__main__":
    sys.stderr.write('playwright.py 进入MCP主循环\n')
    import asyncio
    from agents.mcp import MCPServerStdio
    
    async def _main():
        # 创建Playwright代理
        agent = PlaywrightAgent()
        # 创建MCP服务器
        server = MCPServerStdio(
            name="playwright",
            agent=agent
        )
        await server.serve()
        
    asyncio.run(_main())