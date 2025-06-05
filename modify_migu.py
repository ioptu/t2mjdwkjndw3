import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import time
from tqdm import tqdm  # pip install tqdm
import logging

# 配置日志
logging.basicConfig(filename='errors.log', level=logging.WARNING, format='%(asctime)s - %(message)s')

def get_final_url(url, max_redirects=10, connect_timeout=3, read_timeout=5, retries=3, delay=0.2):
    """
    获取 URL 的最终重定向地址，支持失败重试与限速控制。
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, allow_redirects=False, timeout=(connect_timeout, read_timeout))
            redirect_count = 0

            while redirect_count < max_redirects:
                if response.status_code in (301, 302, 303, 307, 308) and 'Location' in response.headers:
                    new_url = response.headers['Location']
                    if not new_url.startswith(('http://', 'https://')):
                        new_url = urljoin(url, new_url)
                    url = new_url
                    response = requests.get(url, allow_redirects=False, timeout=(connect_timeout, read_timeout))
                    redirect_count += 1
                else:
                    break

            if delay > 0:
                time.sleep(delay)
            return url

        except requests.RequestException as e:
            if attempt == retries:
                logging.warning(f"请求失败 [{url}] (第 {attempt} 次): {e}")
                return url  # 失败时返回原始 URL
            time.sleep(delay)  # 等待后重试

def process_m3u_file(input_file, output_file, max_workers=10, connect_timeout=3, read_timeout=5, delay=0.2):
    """
    处理 M3U 文件，多线程、限速、重试、错误日志等增强功能。
    """
    start_time = time.time()

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    url_pattern = re.compile(r'^https?://\S+')
    url_tasks = []

    # 准备任务
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, line in enumerate(lines):
            if url_pattern.match(line):
                future = executor.submit(
                    get_final_url,
                    line,
                    max_redirects=10,
                    connect_timeout=connect_timeout,
                    read_timeout=read_timeout,
                    retries=3,
                    delay=delay
                )
                futures[future] = i

        # 显示进度
        for future in tqdm(as_completed(futures), total=len(futures), desc="🔁 正在处理链接"):
            i = futures[future]
            lines[i] = future.result()

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\n✅ 所有链接处理完成，耗时 {time.time() - start_time:.2f} 秒")
    print(f"输出文件: {output_file}")
    print(f"如有错误记录，请查看 errors.log")

# 使用示例
if __name__ == "__main__":
    input_m3u = "migu.m3u"
    output_m3u = "final.m3u"
    process_m3u_file(input_m3u, output_m3u, max_workers=5, connect_timeout=5, read_timeout=5, delay=0.3)
