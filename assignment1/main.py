header = bytearray(3)
header[0] = 2 << 6
header[0] = header[0] | 0 << 5
header[0] = header[0] | 0 << 4
header[0] = header[0] | 0
header[1] = 12345 >> 8
header[2] = 12345 & 0xFF
print(header[2])
# lines = []
# for line in header:
#     lines.append(line.decode('utf-8', 'slashescape'))
# print(lines)