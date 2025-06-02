# filename: deduplicate_migu.py

def deduplicate_migu(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    seen = set()
    deduped = []

    i = 0
    while i < len(lines) - 1:
        if lines[i].startswith("#EXTINF"):
            extinf_line = lines[i]
            url_line = lines[i + 1]
            if ',' in extinf_line:
                channel_name = extinf_line.split(',', 1)[1]
                if channel_name not in seen:
                    seen.add(channel_name)
                    deduped.append(extinf_line)
                    deduped.append(url_line)
                    deduped.append("")  # 空行分隔
            i += 2
        else:
            i += 1

    return deduped

if __name__ == "__main__":
    input_file = "migu_output.txt"
    output_file = "migu.m3u"

    unique_entries = deduplicate_migu(input_file)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for line in unique_entries:
            f.write(line + '\n')

    print(f"已生成去重后的 m3u 文件：{output_file}")
