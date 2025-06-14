import argparse

def _check_match(text, keyword_str):
    """
    辅助函数：检查文本是否包含指定关键字，支持 && 和 || 逻辑。
    :param text: 要搜索的文本。
    :param keyword_str: 要搜索的关键字字符串（可含 && 或 ||）。
    :return: 如果匹配则返回 True，否则返回 False。
    """
    if not keyword_str: # 如果关键字为空，则不匹配
        return False

    # 处理关键词中的引号，去除首尾可能存在的双引号
    processed_keyword = keyword_str.strip('"')

    if "&&" in processed_keyword:
        # 逻辑与：所有子关键字都必须包含
        sub_keywords = [k.strip() for k in processed_keyword.split("&&")]
        return all(k in text for k in sub_keywords)
    elif "||" in processed_keyword:
        # 逻辑或：任一子关键字包含即可
        sub_keywords = [k.strip() for k in processed_keyword.split("||")]
        return any(k in text for k in sub_keywords)
    else:
        # 简单匹配：只要包含关键字即可
        return processed_keyword in text

def extract_keyword_lines(filepath, ekeyword=None, ukeyword=None, xkeyword=None,
                          extinf_and_url_keywords=None, extinf_or_url_keywords=None):
    """
    从M3U文件中提取包含指定关键字的记录。
    此版本改进了M3U记录的识别，并支持在不同行类型中搜索。
    同时，它会保留原始文件中匹配记录的顺序，并确保结果不重复。
    :param filepath: 输入文件路径。
    :param ekeyword: 只在 #EXTINF 行中搜索的关键字。
    :param ukeyword: 只在 URL 行中搜索的关键字。
    :param xkeyword: 在 #EXTINF 和 URL 行中同时搜索的关键字。
    :param extinf_and_url_keywords: 逗号分隔的两个关键字，EXTINF行和URL行需同时包含对应关键字。
    :param extinf_or_url_keywords: 逗号分隔的两个关键字，EXTINF行或URL行包含对应关键字。
    :return: 包含匹配记录的列表。
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 使用列表存储匹配到的记录对 (EXTINF行, URL行)，以保留顺序
    ordered_record_pairs = []
    # 使用集合辅助去重，存储已添加的记录对，提高查找效率
    seen_record_pairs = set()

    # 解析组合关键字参数
    kw1_and_kw2 = None
    if extinf_and_url_keywords:
        parts = [k.strip() for k in extinf_and_url_keywords.split(',')]
        if len(parts) == 2:
            kw1_and_kw2 = (parts[0], parts[1])
        else:
            print("错误：--eandu 参数需要两个用逗号分隔的关键字。")
            return []

    kw1_or_kw2 = None
    if extinf_or_url_keywords:
        parts = [k.strip() for k in extinf_or_url_keywords.split(',')]
        if len(parts) == 2:
            kw1_or_kw2 = (parts[0], parts[1])
        else:
            print("错误：--eoru 参数需要两个用逗号分隔的关键字。")
            return []

    i = 0
    while i < len(lines):
        current_line_stripped = lines[i].strip()

        # 检查是否是M3U的描述信息行（通常以 #EXTINF 开头）
        if current_line_stripped.startswith('#EXTINF'):
            # 找到 #EXTINF 行后，尝试获取其下一行作为对应的 URL 行
            if i + 1 < len(lines):
                url_line_stripped = lines[i+1].strip()

                matched = False
                if ekeyword:
                    # 只在 EXTINF 行中搜索
                    matched = _check_match(current_line_stripped, ekeyword)
                elif ukeyword:
                    # 只在 URL 行中搜索
                    matched = _check_match(url_line_stripped, ukeyword)
                elif xkeyword:
                    # 在 EXTINF 或 URL 行中搜索 (任一匹配即可)
                    matched = _check_match(current_line_stripped, xkeyword) or \
                              _check_match(url_line_stripped, xkeyword)
                elif kw1_and_kw2:
                    # EXTINF 包含 kw1 且 URL 包含 kw2
                    matched = _check_match(current_line_stripped, kw1_and_kw2[0]) and \
                              _check_match(url_line_stripped, kw1_and_kw2[1])
                elif kw1_or_kw2:
                    # EXTINF 包含 kw1 或 URL 包含 kw2
                    matched = _check_match(current_line_stripped, kw1_or_kw2[0]) or \
                              _check_match(url_line_stripped, kw1_or_kw2[1])

                if matched:
                    # 如果匹配，且该记录对尚未被添加过
                    current_pair = (current_line_stripped, url_line_stripped)
                    if current_pair not in seen_record_pairs:
                        ordered_record_pairs.append(current_pair)
                        seen_record_pairs.add(current_pair)

                i += 2  # 处理完 #EXTINF 和 URL 两行，跳到下一条记录的开始
            else:
                # 如果 #EXTINF 是文件的最后一行，没有对应的URL行，则跳过此行
                # 这避免了访问 lines[i+1] 时可能出现的 IndexError
                i += 1
        else:
            # 如果当前行不是 #EXTINF 开头，则认为它不是 M3U 记录的起始，直接跳过
            # 我们只关注 #EXTINF 后面跟着 URL 的标准 M3U 格式
            i += 1

    # 将有序且去重后的记录对转换回列表格式，每条记录包括 EXTINF行、URL行 和一个空行
    result = []
    for extinf_line, url_line in ordered_record_pairs:
        result.append(extinf_line)
        result.append(url_line)
        result.append("") # 每条记录后添加一个空行，保持原有的输出格式

    return result

def parse_arguments():
    """
    解析命令行参数。
    支持通过 --ekeyword, --ukeyword, --xkeyword, --eandu, --eoru 选择不同的搜索范围。
    这些参数是互斥的，且必须提供其中一个。
    """
    parser = argparse.ArgumentParser(description='从M3U文件中提取包含指定关键字的记录')
    parser.add_argument('--input', required=True, help='输入M3U文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')

    # 创建一个互斥组，用户只能选择其中一个关键字参数
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ekeyword', help='在 #EXTINF 行中搜索的关键字（可含双引号，支持 && 和 || 逻辑）')
    group.add_argument('--ukeyword', help='在 URL 行中搜索的关键字（可含双引号，支持 && 和 || 逻辑）')
    group.add_argument('--xkeyword', help='在 #EXTINF 和 URL 行中同时搜索的关键字（可含双引号，支持 && 和 || 逻辑）')
    group.add_argument('--eandu', dest='extinf_and_url_keywords', help='EXTINF行包含Keyword1且URL行包含Keyword2（格式："Keyword1,Keyword2"）')
    group.add_argument('--eoru', dest='extinf_or_url_keywords', help='EXTINF行包含Keyword1或URL行包含Keyword2（格式："Keyword1,Keyword2"）')

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    # 根据用户提供的关键字参数调用 extract_keyword_lines
    extracted_lines = []
    search_keyword_display = ""

    if args.ekeyword:
        extracted_lines = extract_keyword_lines(args.input, ekeyword=args.ekeyword)
        search_keyword_display = f"EXTINF行中的 '{args.ekeyword}'"
    elif args.ukeyword:
        extracted_lines = extract_keyword_lines(args.input, ukeyword=args.ukeyword)
        search_keyword_display = f"URL行中的 '{args.ukeyword}'"
    elif args.xkeyword:
        extracted_lines = extract_keyword_lines(args.input, xkeyword=args.xkeyword)
        search_keyword_display = f"EXTINF或URL行中的 '{args.xkeyword}'"
    elif args.extinf_and_url_keywords: # 注意这里要用 dest 指定的参数名
        extracted_lines = extract_keyword_lines(args.input, extinf_and_url_keywords=args.extinf_and_url_keywords)
        search_keyword_display = f"EXTINF和URL行组合搜索 '{args.extinf_and_url_keywords}'"
    elif args.extinf_or_url_keywords: # 注意这里要用 dest 指定的参数名
        extracted_lines = extract_keyword_lines(args.input, extinf_or_url_keywords=args.extinf_or_url_keywords)
        search_keyword_display = f"EXTINF或URL行组合搜索 '{args.extinf_or_url_keywords}'"

    # 将提取出的行写入输出文件
    with open(args.output, 'w', encoding='utf-8') as f:
        for line in extracted_lines:
            f.write(line + '\n')

    # 打印提取结果的汇总信息
    # 由于每条记录包含 EXTINF 行、URL 行和空行，所以记录总数是列表长度除以 3
    print(f"已提取 {len(extracted_lines)//3} 条包含 {search_keyword_display} 的记录到 {args.output}")
