def process_txt_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(output_file, 'w', encoding='utf-8') as f_out:
        for i in range(1, len(lines), 2):
            line = lines[i].strip()
            f_out.write(f"{line},")
            if i % 20 == 1:  # Adjusted to write a newline every 10 pairs (2 lines each)
                f_out.write("\n")

    print("处理完成！")

# 替换为你的输入文件路径
input_file = './input.txt'
# 替换为你的输出文件路径
output_file = './output.txt'

process_txt_file(input_file, output_file)
