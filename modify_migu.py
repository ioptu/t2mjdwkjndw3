import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def get_final_url(url, max_redirects=5, timeout=5):
    """
    获取 URL 的最终重定向地址（支持多线程）
    :param url: 原始 URL
    :param max_redirects: 最大重定向次数
    :param timeout: 请求超时时间（秒）
    :return: 最终 URL（如果失败则返回原始 URL）
    """
    try:
        response = requests.get(url, allow_redirects=False, timeout=timeout)
        redirect_count = 0
        
        while redirect_count < max_redirects:
            if response.status_code in (301, 302, 303, 307, 308) and 'Location' in response.headers:
                new_url = response.headers['Location']
                # 处理相对路径重定向（如 Location: /new-path）
                if not new_url.startswith(('http://', 'https://')):
                    from urllib.parse import urljoin
                    new_url = urljoin(url, new_url)
                url = new_url
                response = requests.get(url, allow_redirects=False, timeout=timeout)
                redirect_count += 1
            else:
                break
        
        return url
    except requests.RequestException as e:
        print(f"⚠️ 请求失败: {url} ({type(e).__name__}: {e})")
        return url  # 失败时返回原 URL

def process_m3u_file(input_file, output_file, max_workers=10, timeout=5):
    """
    处理 M3U 文件（多线程优化版）
    :param input_file: 输入 M3U 文件路径
    :param output_file: 输出 M3U 文件路径
    :param max_workers: 线程池大小
    :param timeout: 单个 URL 请求超时时间（秒）
    """
    start_time = time.time()
    
    # 读取原始文件
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    # 预编译正则表达式（匹配 URL 行）
    url_pattern = re.compile(r'^https?://\S+')

    # 多线程处理所有 URL
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, line in enumerate(lines):
            if url_pattern.match(line):
                future = executor.submit(get_final_url, line, 10, timeout)
                futures[future] = i  # 记录行号

        # 按完成顺序更新结果
        for future in as_completed(futures):
            line_num = futures[future]
            final_url = future.result()
            lines[line_num] = final_url
            print(f"✅ 处理完成: {lines[line_num]}")

    # 写入新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\n🎉 处理完成！耗时 {time.time() - start_time:.2f} 秒")
    print(f"原始文件: {input_file} → 输出文件: {output_file}")

# 使用示例
if __name__ == "__main__":
    input_m3u = "migu.m3u"    # 输入文件路径
    output_m3u = "final.m3u"      # 输出文件路径
    process_m3u_file(input_m3u, output_m3u, max_workers=2, timeout=10)
