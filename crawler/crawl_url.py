import argparse
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm.auto import tqdm

# ================== HÀM CŨ CỦA BẠN ==================

def get_links_from_page(html: str, base_url: str, item_selector: str, link_selector: str = "a"):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(item_selector)
    links = []

    for item in items:
        # loại bỏ item dạng quảng cáo có class "viewAds-{number}"
        classes = item.get("class", [])
        if any(cls.startswith("viewAds-") for cls in classes):
            continue

        a_tag = item.select_one(link_selector)
        if not a_tag or not a_tag.get("href"):
            continue

        href = urljoin(base_url, a_tag["href"])
        links.append(href)

    return links


def safe_get(
    url: str,
    headers: dict,
    page: int | None = None,
    max_retries: int = 5,
    timeout: int = 15,
) -> requests.Response | None:
    """
    Wrapper cho requests.get với retry khi:
      - HTTP 429 (Too Many Requests) -> tôn trọng Retry-After nếu có
      - Lỗi 5xx
      - Lỗi mạng tạm thời (RequestException)
    """
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
        except requests.RequestException as e:
            print(f"[WARN] Lỗi mạng tại page {page} (attempt {attempt}/{max_retries}): {e}")
            # backoff nhẹ rồi thử lại
            wait = 3 * attempt
            print(f"       -> Đợi {wait}s rồi retry")
            time.sleep(wait)
            continue

        # HTTP 429: Too Many Requests
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = int(retry_after)
                except ValueError:
                    # Nếu Retry-After không phải int (có thể là date), dùng backoff mặc định
                    wait = 5 * attempt
            else:
                wait = 5 * attempt

            print(
                f"[429] Too Many Requests tại page {page} "
                f"(attempt {attempt}/{max_retries}) -> Đợi {wait}s rồi retry"
            )
            time.sleep(wait)
            continue

        # 5xx: server lỗi -> backoff rồi retry
        if 500 <= resp.status_code < 600:
            wait = 3 * attempt
            print(
                f"[{resp.status_code}] Server error tại page {page} "
                f"(attempt {attempt}/{max_retries}) -> Đợi {wait}s rồi retry"
            )
            time.sleep(wait)
            continue

        # Các code khác (200, 4xx không phải 429) -> trả về luôn,
        # để layer bên ngoài quyết định stop hay xử lý tiếp.
        return resp

    print(f"[STOP] Fail sau {max_retries} lần retry tại page {page}, url={url}")
    return None


def crawl_paginated_list(
    base_url_template: str,
    item_selector: str,
    start_page: int = 1,
    max_pages: int | None = None,
    link_selector: str = "a",
    progress_desc: str | None = None,
):
    """
    Crawl list phân trang, có handle HTTP 429 và lỗi mạng tạm thời.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; CrankyCrawler/1.0)"}
    all_links = []

    # Nếu có max_pages -> dùng for + tqdm
    if max_pages is not None:
        page_iter = tqdm(
            range(start_page, max_pages + 1),
            desc=progress_desc or "Pages",
            leave=False,
        )
        for page in page_iter:
            url = base_url_template.format(page=page)

            resp = safe_get(url, headers=headers, page=page)
            if resp is None:
                # Đã retry hết mà vẫn fail -> dừng hẳn range này
                print(f"[STOP] Dừng crawl tại page {page} (không lấy được response).")
                break

            if resp.status_code != 200:
                print(f"[STOP] HTTP {resp.status_code} tại page {page}")
                break

            page_links = get_links_from_page(
                resp.text,
                base_url=url,
                item_selector=item_selector,
                link_selector=link_selector,
            )

            if not page_links:
                print(f"[STOP] Không còn item tại page {page}")
                break

            all_links.extend(page_links)
    else:
        # Trường hợp không giới hạn page (hiếm dùng)
        page = start_page
        while True:
            url = base_url_template.format(page=page)
            resp = safe_get(url, headers=headers, page=page)
            if resp is None:
                print(f"[STOP] Dừng crawl tại page {page} (không lấy được response).")
                break

            if resp.status_code != 200:
                print(f"[STOP] HTTP {resp.status_code} tại page {page}")
                break

            page_links = get_links_from_page(
                resp.text,
                base_url=url,
                item_selector=item_selector,
                link_selector=link_selector,
            )

            if not page_links:
                print(f"[STOP] Không còn item tại page {page}")
                break

            all_links.extend(page_links)
            page += 1

    # dedupe, giữ thứ tự
    all_links = list(dict.fromkeys(all_links))
    return all_links


# ================== CHIẾN THUẬT CHIA KHOẢNG NGÀY ==================

MIN_DATE_STR = "01/12/2020"   # ngày sớm nhất
MAX_DATE_STR = "18/12/2025"   # ngày bắt đầu crawl (đi lùi về trước)
MAX_PAGE_PER_RANGE = 20       # mỗi query chỉ crawl tối đa 20 page

def generate_month_ranges(end_date_str: str = MAX_DATE_STR,
                          min_date_str: str = MIN_DATE_STR):
    """
    Sinh list các khoảng (bdate_str, edate_str), mỗi khoảng ~1 tháng,
    đi lùi từ end_date về min_date.
    edate_{i+1} = bdate_i.
    """
    end_date = datetime.strptime(end_date_str, "%d/%m/%Y")
    min_date = datetime.strptime(min_date_str, "%d/%m/%Y")

    ranges: list[tuple[str, str]] = []
    current_end = end_date

    while current_end > min_date:
        current_start = current_end - relativedelta(months=1)
        if current_start < min_date:
            current_start = min_date

        bdate_str = current_start.strftime("%d/%m/%Y")
        edate_str = current_end.strftime("%d/%m/%Y")
        ranges.append((bdate_str, edate_str))

        # lần sau: edate_new = bdate_old
        current_end = current_start

    return ranges


# ================== CRAWL THEO DATE RANGE + PAGINATION ==================

def crawl_thuvienphapluat_by_ranges(
    item_selector: str,
    link_selector: str = "a",
    min_date_str: str = MIN_DATE_STR,
    max_date_str: str = MAX_DATE_STR,
    max_page_per_range: int = MAX_PAGE_PER_RANGE,
):
    """
    Crawl tất cả link văn bản bằng cách chia nhỏ khoảng ngày (~1 tháng),
    mỗi khoảng query tối đa max_page_per_range trang.
    """
    all_links: list[str] = []
    date_ranges = generate_month_ranges(
        end_date_str=max_date_str,
        min_date_str=min_date_str
    )

    # Nếu muốn crawl từ cũ -> mới:
    # date_ranges = list(reversed(date_ranges))

    # Progress bar cho date ranges
    for idx, (bdate, edate) in enumerate(
        tqdm(date_ranges, desc="Date ranges", unit="range"), start=1
    ):
        print(f"\n===== RANGE {idx}: {bdate} -> {edate} =====")

        base_url_template = (
            "https://thuvienphapluat.vn/page/tim-van-ban.aspx"
            "?keyword=&area=0&match=True&type=0&status=0&signer=0"
            f"&bdate={bdate}&edate={edate}&sort=1&lan=1&scan=0&org=1&fields=&page={{page}}"
        )

        range_links = crawl_paginated_list(
            base_url_template=base_url_template,
            item_selector=item_selector,
            start_page=1,
            max_pages=max_page_per_range,
            link_selector=link_selector,
            progress_desc=f"Pages {bdate}→{edate}",
        )
        print(f"[RANGE DONE] {bdate} -> {edate}: lấy được {len(range_links)} link")

        all_links.extend(range_links)

    # dedupe toàn bộ link
    all_links = list(dict.fromkeys(all_links))
    print(f"\n[TOTAL] Tổng số link unique: {len(all_links)}")
    return all_links


# ================== ARGPARSE ==================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Crawler ThuVienPhapLuat by date ranges"
    )

    parser.add_argument(
        "--min-date",
        type=str,
        default=MIN_DATE_STR,
        help="Ngày bắt đầu xa nhất (dd/MM/yyyy)",
    )

    parser.add_argument(
        "--max-date",
        type=str,
        default=MAX_DATE_STR,
        help="Ngày kết thúc gần nhất (dd/MM/yyyy)",
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=MAX_PAGE_PER_RANGE,
        help="Số page tối đa mỗi query date-range",
    )

    parser.add_argument(
        "--item-selector",
        type=str,
        required=True,
        help="CSS selector để lấy item chứa link văn bản",
    )

    parser.add_argument(
        "--link-selector",
        type=str,
        default="a",
        help="CSS selector để lấy link bên trong item",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path file để lưu tất cả link (nếu muốn)",
    )

    return parser.parse_args()


# ================== MAIN ==================

def main():
    args = parse_args()

    links = crawl_thuvienphapluat_by_ranges(
        item_selector=args.item_selector,
        link_selector=args.link_selector,
        min_date_str=args.min_date,
        max_date_str=args.max_date,
        max_page_per_range=args.max_pages,
    )

    print("\n=== DONE CRAWL ===")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            for link in links:
                f.write(link + "\n")
        print(f">>> Saved {len(links)} links to {args.output}")
    else:
        for link in links:
            print(link)


if __name__ == "__main__":
    main()
