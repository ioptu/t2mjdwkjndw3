import argparse

def extract_keyword_lines(filepath, keyword):
    """
    从M3U文件中提取包含指定关键字的记录
    :param filepath: 输入文件路径
    :param keyword: 要搜索的关键字（可含双引号）
    :return: 包含匹配记录的列表
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    result = []
    i = 0
    while i < len(lines) - 1:
        line = lines[i]
        # 支持 && 和 || 逻辑
        if "&&" in keyword:
            match = all(k.strip() in line for k in keyword.split("&&"))
        elif "||" in keyword:
            match = any(k.strip() in line for k in keyword.split("||"))
        else:
            match = keyword in line
        
        if match:
            result.append(line.strip())
            result.append(lines[i + 1].strip())
            result.append("")
            i += 2
        else:
            i += 1
    return result

def parse_arguments():
    """
    解析命令行参数（自动处理含引号的情况）
    """
    parser = argparse.ArgumentParser(description='从M3U文件中提取包含指定关键字的记录')
    parser.add_argument('--input', required=True, help='输入M3U文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--keyword', required=True, help='要搜索的关键字（可含双引号）')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    extracted = extract_keyword_lines(args.input, args.keyword)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        for line in extracted:
            f.write(line + '\n')

    print(f"已提取 {len(extracted)//3} 条包含 '{args.keyword}' 的记录到 {args.output}")
