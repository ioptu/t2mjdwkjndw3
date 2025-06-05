import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from urllib.parse import urljoin

def get_final_url(url, max_redirects=10, timeout=5):
    try:
        response = requests.get(url, allow_redirects=False, timeout=timeout)
        redirect_count = 0

        while redirect_count < max_redirects:
            if response.status_code in (301, 302, 303, 307, 308) and 'Location' in response.headers:
                new_url = response.headers['Location']
                if not new_url.startswith(('http://', 'https://')):
                    new_url = urljoin(url, new_url)
                url = new_url
                response = requests.get(url, allow_redirects=False, timeout=timeout)
                redirect_count += 1
            else:
                break

        return url
    except requests.RequestException as e:
        print(f"⚠️ 请求失败: {url} ({type(e).__name__}: {e})")
        return None

def resolve_urls(lines, url_pattern, max_workers=10, timeout=5):
    new_lines = lines[:]
    failed = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, line in enumerate(lines):
            if url_pattern.match(line):
                future = executor.submit(get_final_url, line, 10, timeout)
                futures[future] = i

        for future in as_completed(futures):
            idx = futures[future]
            result = future.result()
            if result:
                new_lines[idx] = result
                print(f"✅ 成功: {result}")
            else:
                failed[idx] = lines[idx]
                print(f"❌ 失败: {lines[idx]}")

    return new_lines, failed

def process_m3u_file(input_file, output_file, max_workers=10, timeout=5, max_retries=3):
    start_time = time.time()

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    url_pattern = re.compile(r'^https?://\S+')

    lines, failed = resolve_urls(lines, url_pattern, max_workers, timeout)

    retry_count = 0
    while failed and retry_count < max_retries:
        retry_count += 1
        print(f"\n🔁 第 {retry_count} 次重试，共 {len(failed)} 个失败请求...")
        time.sleep(10)

        retry_lines = [failed[i] if i in failed else '' for i in range(len(lines))]
        retry_result, retry_failed = resolve_urls(retry_lines, url_pattern, max_workers, timeout)

        for i in failed:
            if retry_result[i]:
                lines[i] = retry_result[i]

        failed = {i: failed[i] for i in failed if retry_result[i] is None}

    if failed:
        print(f"\n⚠️ 以下 {len(failed)} 个请求在重试 {max_retries} 次后仍失败，将保留原始链接：")
        for idx, url in failed.items():
            lines[idx] = url
            print(f" - {url}")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\n🎉 全部处理完成！总耗时 {time.time() - start_time:.2f} 秒")
    print(f"原始文件: {input_file} → 输出文件: {output_file}")

# 使用示例
if __name__ == "__main__":
    input_m3u = "migu.m3u"
    output_m3u = "final.m3u"
    process_m3u_file(input_m3u, output_m3u, max_workers=5, timeout=10, max_retries=6)
