import asyncio
import random
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def human_delay(min_s: float = 1.8, max_s: float = 4.5):
    """Delay ngẫu nhiên cho giống hành vi người dùng."""
    await asyncio.sleep(random.uniform(min_s, max_s))


async def crawl_paginated_list(
    page,
    base_url_template: str,
    item_selector: str,
    link_selector: str = "a",
    start_page: int = 1,
    max_pages: int | None = None,  # None = crawl đến khi hết item
):
    all_links: list[str] = []
    current_page = start_page

    while True:
        if max_pages is not None and current_page > max_pages:
            print(f"[STOP] đạt max_pages = {max_pages}")
            break

        url = base_url_template.format(page=current_page)
        print(f"[PAGE] {current_page} -> {url}")
        await human_delay()

        await page.goto(url, wait_until="networkidle", timeout=60000)

        # giả behavior người dùng: delay + scroll
        await human_delay(0.8, 2.0)
        await page.mouse.wheel(0, random.randint(350, 900))
        await human_delay(0.4, 1.2)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        items = soup.select(item_selector)
        print(f"  -> found {len(items)} items")

        # nếu không còn item -> dừng
        if not items:
            print("[STOP] không còn item → kết thúc crawl")
            break

        page_links: list[str] = []
        for item in items:
            a_tag = item.select_one(link_selector)
            if not a_tag or not a_tag.get("href"):
                continue
            href = urljoin(url, a_tag["href"])
            page_links.append(href)

        if not page_links:
            print(f"[STOP] page {current_page} không có link → dừng")
            break

        all_links.extend(page_links)
        current_page += 1

    # loại trùng
    all_links = list(dict.fromkeys(all_links))
    print(f"[DONE] total links: {len(all_links)}")
    return all_links


async def main():
    # ---- cấu hình riêng cho thuvienphapluat ----
    base_url_template = (
        "https://thuvienphapluat.vn/page/searchlegal.aspx"
        "?keyword=&area=0&match=True&type=0&status=0&signer=0"
        "&bdate=01/12/2020&sort=1&lan=1&scan=0&org=1&fields=&page={page}"
    )
    # item list mỗi văn bản nằm trong 1 <div> (bạn có thể chỉnh lại nếu HTML khác)
    item_selector = "#block-info-advan > div:nth-child(2) > div"

    # ---- đúng pattern recommend của playwright_stealth ----
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=False)  # True nếu không cần xem
        context = await browser.new_context()
        page = await context.new_page()

        urls = await crawl_paginated_list(
            page=page,
            base_url_template=base_url_template,
            item_selector=item_selector,
            link_selector="a",
            start_page=1,
            max_pages=None,  # hoặc ví dụ 10 nếu muốn giới hạn
        )

        await browser.close()

    print("\n=== RESULT ===")
    for u in urls:
        print(u)


if __name__ == "__main__":
    asyncio.run(main())
