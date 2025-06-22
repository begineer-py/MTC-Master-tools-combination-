#!/bin/bash

echo "正在檢查暫存區中的檔案大小..."
echo "大小 (Bytes)  路徑"
echo "------------  ----"

# 1. 使用 git ls-files -s 列出暫存區檔案的 mode, SHA-1, stage number 和路徑
# 2. 對於每一行：
#    a. 提取 SHA-1 (第二個欄位) 和路徑 (第四個欄位及之後，處理檔名中可能存在的空格)
#    b. 使用 git cat-file -s <SHA-1> 獲取該 blob 物件的實際大小 (bytes)
#    c. 輸出大小和路徑
# 3. 使用 sort -nr 按照大小（數字，反向）排序
# 4. (可選) 使用 head -n <數量> 顯示最大的前 N 個檔案
# 5. (可選) 使用 awk 或 numfmt 格式化輸出大小為人類可讀格式

git ls-files -s | while IFS=$'\t' read -r mode_sha_stage path; do
    # mode_sha_stage 格式是 "mode SHA1 stage_number"
    # 我們需要從中提取 SHA1
    # 例如："100644 8f81583850594371999971933e89a50209503957 0"
    sha1=$(echo "$mode_sha_stage" | awk '{print $2}')
    
    # 獲取 blob 物件的大小
    size_bytes=$(git cat-file -s "$sha1")
    
    # 輸出原始大小和路徑，以便後續排序
    echo "$size_bytes $path"
done | \
sort -nr | \
head -n 20 | \
awk '{
    size = $1;
    # 重新組合路徑，因為路徑本身可能包含空格
    filepath = "";
    for (i = 2; i <= NF; i++) {
        filepath = filepath (i == 2 ? "" : " ") $i;
    }

    # 轉換為人類可讀格式 (可選)
    hr_size = size;
    unit = "B";
    if (hr_size > 1024) { hr_size /= 1024; unit = "KiB"; }
    if (hr_size > 1024) { hr_size /= 1024; unit = "MiB"; }
    if (hr_size > 1024) { hr_size /= 1024; unit = "GiB"; }
    
    if (unit == "B") {
        printf "%10d %s  %s\n", hr_size, unit, filepath;
    } else {
        printf "%9.2f %s  %s\n", hr_size, unit, filepath;
    }
}'

echo "------------  ----"
echo "檢查完成。"