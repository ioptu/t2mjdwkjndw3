import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading
from urllib.parse import urljoin

# 限速配置
lock = threading.Lock()
request_timestamps = []
REQUESTS_PER_SECOND = 5  # 每秒最多请求数

def rate_limited():
    """控制请求速率，避免过快访问目标网站"""
    with lock:
        now = time.time()
        while request_timestamps and now - request_timestamps[0] > 1:
            request_timestamps.pop(0)
        if len(request_timestamps) >= REQUESTS_PER_SECOND:
            wait_time = 1 - (now - request_timestamps[0])
            time.sleep(wait_time)
        request_timestamps.append(time.time())

def get_final_url(url, max_redirects=10, timeout=5, retries=3, retry_delay=1):
    """
    获取 URL 的最终重定向地址，支持失败重试与节流
    """
    for attempt in range(1, retries + 1):
        try:
            rate_limited()
            response = requests.get(url, allow_redirects=False, timeout=timeout)
            redirect_count = 0

            while redirect_count < max_redirects:
                if response.status_code in (301, 302, 303, 307, 308) and 'Location' in response.headers:
                    new_url = response.headers['Location']
                    if not new_url.startswith(('http://', 'https://')):
                        new_url = urljoin(url, new_url)
                    url = new_url
                    rate_limited()
                    response = requests.get(url, allow_redirects=False, timeout=timeout)
                    redirect_count += 1
                else:
                    break
            return url

        except requests.RequestException as e:
            print(f"⚠️ 第 {attempt} 次请求失败: {url} ({type(e).__name__}: {e})")
            if attempt < retries:
                time.sleep(retry_delay)
            else:
                return url  # 最后一次失败，返回原始 URL

def process_m3u_file(input_file, output_file, max_workers=10, timeout=5, retries=3, retry_delay=1):
    """
    多线程处理 M3U 文件，支持限速与重试
    """
    start_time = time.time()

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    url_pattern = re.compile(r'^https?://\S+')

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, line in enumerate(lines):
            if url_pattern.match(line):
                future = executor.submit(get_final_url, line, 10, timeout, retries, retry_delay)
                futures[future] = i

        for future in as_completed(futures):
            line_num = futures[future]
            final_url = future.result()
            lines[line_num] = final_url
            print(f"✅ 处理完成: {final_url}")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\n🎉 处理完成！耗时 {time.time() - start_time:.2f} 秒")
    print(f"原始文件: {input_file} → 输出文件: {output_file}")

if __name__ == "__main__":
    input_m3u = "migu.m3u"
    output_m3u = "final.m3u"
    process_m3u_file(input_m3u, output_m3u,
                     max_workers=5,
                     timeout=10,
                     retries=3,
                     retry_delay=1)  # 设置每次重试间隔 2 秒
