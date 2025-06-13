import argparse

def deduplicate_m3u(filepath):
    """
    对M3U文件进行去重处理（基于频道名称）
    :param filepath: 输入文件路径
    :return: 去重后的条目列表
    """
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

def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(
        description='M3U文件去重工具',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='输入M3U文件路径',
        metavar='FILE'
    )
    parser.add_argument(
        '-o', '--output',
        default='output.m3u',
        help='输出M3U文件路径',
        metavar='FILE'
    )
    parser.add_argument(
        '--no-extm3u',
        action='store_false',
        dest='add_header',
        help='不在输出文件中添加#EXTM3U头'
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    unique_entries = deduplicate_m3u(args.input)

    with open(args.output, 'w', encoding='utf-8') as f:
        if args.add_header:
            f.write("#EXTM3U\n")
        for line in unique_entries:
            f.write(line + '\n')

    print(f"已处理: {args.input}")
    print(f"去重后: {len(unique_entries)//3} 个频道")
    print(f"输出到: {args.output}")
