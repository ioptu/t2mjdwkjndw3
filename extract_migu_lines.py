# filename: extract_migu_lines.py

def extract_migu_lines(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    result = []
    i = 0
    while i < len(lines) - 1:
        if "咪咕视频" in lines[i]:
            result.append(lines[i].strip())
            result.append(lines[i + 1].strip())
            result.append("")  # 空行分隔方便阅读
            i += 2  # 跳过已处理的下一行
        else:
            i += 1

    return result

if __name__ == "__main__":
    input_file = "miguraw.m3u"  # 替换为你的文件名
    output_file = "migu_output.txt"

    extracted = extract_migu_lines(input_file)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in extracted:
            f.write(line + '\n')

    print(f"已提取 {len(extracted) // 3} 条咪咕视频记录到 {output_file}")
