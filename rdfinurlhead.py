import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from urllib.parse import urljoin
import sys
import argparse

def get_final_url(url, max_redirects=10, timeout=5):
    """
    获取 URL 的最终重定向地址，并在获取到响应头后检查 Content-Type。
    如果检测到视频内容，则中止下载响应体。
    """
    current_url = url
    redirect_count = 0

    try:
        while redirect_count < max_redirects:
            # 初始请求，allow_redirects=False 来手动处理重定向
            response = requests.get(current_url, allow_redirects=False, timeout=timeout, stream=True) # stream=True 关键
            response.raise_for_status() # 检查HTTP状态码，如果不是2xx，则抛出异常

            if response.status_code in (301, 302, 303, 307, 308) and 'Location' in response.headers:
                new_url = response.headers['Location']
                if not new_url.startswith(('http://', 'https://')):
                    new_url = urljoin(current_url, new_url)
                current_url = new_url
                redirect_count += 1
                # 在重定向时关闭当前响应的连接
                response.close()
            else:
                # 到达最终URL，或者不再重定向
                final_url = current_url
                content_type = response.headers.get('Content-Type', '').lower()
                print(f"最终URL: {final_url}")
                print(f"Content-Type: {content_type}")

                if 'video/' in content_type or 'application/octet-stream' in content_type: # 某些FLV可能没有明确的video/flv
                    print("检测到视频内容，中止响应体下载。")
                    response.close() # 立即关闭连接，中止下载
                    return final_url, True, True # 返回最终URL，成功，是视频
                else:
                    # 如果不是视频，你可以选择继续处理响应体，或者直接关闭
                    response.close() # 如果不需要响应体内容，也可以直接关闭
                    return final_url, True, False # 返回最终URL，成功，不是视频

    except requests.exceptions.RequestException as e:
        print(f"⚠️ 请求失败: {current_url} ({type(e).__name__}: {e})")
        return current_url, False, False # 返回当前URL，失败，不是视频

def resolve_urls_with_retry(urls, max_workers=10, timeout=5, max_retries=3, delay_between_retries=10):
    """
    解析URL，失败后延迟重试，最多尝试 max_retries 次
    """
    resolved_urls = {}
    retries = 0

    while retries <= max_retries:
        print(f"\n🔄 开始第 {retries+1} 轮处理...")
        failed_urls = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(get_final_url, url, 10, timeout): url for url in urls}

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                final_url, success = future.result()
                resolved_urls[url] = final_url
                if success:
                    print(f"✅ 成功: {final_url}")
                else:
                    print(f"❌ 失败: {url}")
                    failed_urls.append(url)

        if not failed_urls:
            break  # 全部成功，跳出循环
        if retries == max_retries:
            print("\n❗已达最大重试次数，以下 URL 仍处理失败：")
            for url in failed_urls:
                print(url)
            break

        print(f"\n⏳ 等待 {delay_between_retries} 秒后重新尝试 {len(failed_urls)} 个失败的请求...")
        time.sleep(delay_between_retries)
        urls = failed_urls
        retries += 1

    return resolved_urls

def process_m3u_file(input_file, output_file, max_workers=10, timeout=5, max_retries=3):
    """
    处理 M3U 文件，解析所有 URL，自动重试失败项
    """
    start_time = time.time()

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    url_pattern = re.compile(r'^https?://\S+')
    url_to_line_indices = {}
    urls = []

    for i, line in enumerate(lines):
        if url_pattern.match(line):
            urls.append(line)
            url_to_line_indices.setdefault(line, []).append(i)

    resolved_map = resolve_urls_with_retry(
        urls, max_workers=max_workers, timeout=timeout, max_retries=max_retries, delay_between_retries=10
    )

    for original_url, final_url in resolved_map.items():
        for i in url_to_line_indices[original_url]:
            lines[i] = final_url

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\n🎉 所有任务完成，总耗时 {time.time() - start_time:.2f} 秒")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")

def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='处理M3U文件中的URL重定向')
    parser.add_argument('--input', required=True, help='输入M3U文件路径')
    parser.add_argument('--output', required=True, help='输出M3U文件路径')
    parser.add_argument('--workers', type=int, default=5, help='最大工作线程数 (默认: 5)')
    parser.add_argument('--timeout', type=int, default=10, help='请求超时时间(秒) (默认: 10)')
    parser.add_argument('--retries', type=int, default=5, help='最大重试次数 (默认: 5)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    process_m3u_file(
        input_file=args.input,
        output_file=args.output,
        max_workers=args.workers,
        timeout=args.timeout,
        max_retries=args.retries
    )
