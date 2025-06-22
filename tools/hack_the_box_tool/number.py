import sys
import math

# 設定Python可以處理的最大整數字串長度
sys.set_int_max_str_digits(0)  # 0表示無限制

print("=== 產生極大數字的幾種方法 ===\n")
print("🚀 既然有32GB記憶體，我們就來產生真正的超級巨大數字！")

# 準備寫入檔案的內容
output_content = []

# 方法1: 超大指數運算
print("1. 超大指數運算法:")
huge_number_1 = 10**10000  # 10的10000次方
print(f"10^10000 = {str(huge_number_1)[:50]}...（共{len(str(huge_number_1))}位數）")
output_content.append(f"{huge_number_1}\n\n")

# 方法2: 超大階乘運算
print("\n2. 超大階乘運算法:")
huge_number_2 = math.factorial(1000)  # 1000的階乘
print(f"1000! = {str(huge_number_2)[:50]}...（共{len(str(huge_number_2))}位數）")
output_content.append(f"{huge_number_2}\n\n")

# 方法3: 超長字串數字
print("\n3. 超長字串數字法:")
huge_number_3 = int("9" * 100000)  # 100000個9組成的數字
print(f"100000個9組成的數 = {str(huge_number_3)[:50]}...（共{len(str(huge_number_3))}位數）")
output_content.append(f"{huge_number_3}\n\n")

# 方法4: 超大指數塔
print("\n4. 超大指數塔法:")
huge_number_4 = 2**(2**20)  # 2^(2^20) = 2^1048576
print(f"2^(2^20) 的位數約為: {2**20 * math.log10(2):.0f} 位")
# 實際計算這個超大數字
output_content.append(f"{huge_number_4}\n\n")

# 方法5: 多重階乘相乘
print("\n5. 多重階乘相乘:")
huge_number_5 = math.factorial(500) * math.factorial(600) * math.factorial(700)
print(f"500! × 600! × 700! = {str(huge_number_5)[:50]}...（共{len(str(huge_number_5))}位數）")
output_content.append(f"{huge_number_5}\n\n")

# 方法6: 超大質數相關
print("\n6. 超大質數相關:")
huge_number_6 = (2**31 - 1) ** 1000  # 梅森質數的1000次方
print(f"(2^31-1)^1000 = {str(huge_number_6)[:50]}...（共{len(str(huge_number_6))}位數）")
output_content.append(f"{huge_number_6}\n\n")

# 方法7: 組合超大數字
print("\n7. 組合超大數字:")
huge_number_7 = int("123456789" * 50000)  # 重複50000次的123456789
print(f"123456789重複50000次 = {str(huge_number_7)[:50]}...（共{len(str(huge_number_7))}位數）")
output_content.append(f"{huge_number_7}\n\n")

# 方法8: 超級指數運算
print("\n8. 超級指數運算:")
huge_number_8 = 7**(7**7)  # 7^(7^7) = 7^823543
print(f"7^(7^7) = {str(huge_number_8)[:50]}...（共{len(str(huge_number_8))}位數）")
output_content.append(f"{huge_number_8}\n\n")

# 方法9: 超大連乘積
print("\n9. 超大連乘積:")
huge_number_9 = 1
for i in range(1, 1001):  # 1到1000的連乘積
    huge_number_9 *= i
print(f"1×2×3×...×1000 = {str(huge_number_9)[:50]}...（共{len(str(huge_number_9))}位數）")
output_content.append(f"{huge_number_9}\n\n")

# 方法10: 終極巨大數字
print("\n10. 終極巨大數字:")
huge_number_10 = int("9876543210" * 100000)  # 重複100000次
print(f"9876543210重複100000次 = {str(huge_number_10)[:50]}...（共{len(str(huge_number_10))}位數）")
output_content.append(f"{huge_number_10}\n\n")

# 計算總字元數
total_chars = len(''.join(output_content))
print(f"\n📊 總共產生了 {total_chars:,} 個字元的超級巨大數字！")

# 將所有極大數字寫入檔案
try:
    print("\n💾 正在寫入 number.txt 檔案...")
    with open('number.txt', 'w', encoding='utf-8') as f:
        f.writelines(output_content)
    print(f"✅ 成功將所有超級極大數字寫入 number.txt 檔案！")
    print(f"📁 檔案大小約為 {total_chars:,} 個字元 ({total_chars/1024/1024:.2f} MB)")
except Exception as e:
    print(f"❌ 寫入檔案時發生錯誤: {e}")

print("\n=== 32GB記憶體的威力展現 ===")
print("🌌 這些數字比可觀測宇宙中的原子數量還要大！")
print("⭐ 如果每個數字都是一顆星星，我們剛剛創造了無數個宇宙！")
print("🚀 這就是32GB記憶體的超級計算能力！")