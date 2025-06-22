#!/bin/bash

# 定義字典存放的路徑
WORDLISTS_DIR="./payloads/dirb"

# 定義滲透測試常用的字典文件URL列表
declare -a WORDLIST_URLS=(
    "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt"
    "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/raft-large-words.txt"
    "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/big.txt"
)

echo "[*] 正在設置字典文件..."

# 檢查 payloads/dirb 目錄是否存在，如果不存在則創建
if [ ! -d "$WORDLISTS_DIR" ]; then
    echo "[*] 目錄 '$WORDLISTS_DIR' 不存在，正在創建..."
    mkdir -p "$WORDLISTS_DIR"
    if [ $? -ne 0 ]; then
        echo "[!] 錯誤：無法創建目錄 '$WORDLISTS_DIR'。請檢查權限。"
        exit 1
    fi
    echo "[+] 目錄 '$WORDLISTS_DIR' 創建成功。"
else
    echo "[*] 目錄 '$WORDLISTS_DIR' 已存在。"
fi

# 檢查是否安裝了 aria2c
if command -v aria2c &> /dev/null
then
    DOWNLOAD_CMD="aria2c -x 16 -s 16 -k 1M -d \"$WORDLISTS_DIR\" -o"
    DOWNLOAD_TYPE="多線程"
else
    DOWNLOAD_CMD="wget -q --show-progress -O"
    DOWNLOAD_TYPE="單線程"
    echo "[!] aria2c 未安裝。aria2c 是一個多線程下載工具，建議安裝以加快字典下載速度。"
    echo "請運行以下命令安裝: sudo apt install aria2"
    echo "[*] 正在嘗試使用 wget 替代下載..."
fi

# 遍歷URL列表並下載每個字典文件
for URL in "${WORDLIST_URLS[@]}"; do
    FILENAME=$(basename "$URL")
    TARGET_FILE_PATH="$WORDLISTS_DIR/$FILENAME"

    echo "[*] 正在下載 $FILENAME 到 '$WORDLISTS_DIR' ($DOWNLOAD_TYPE)..."

    if [ "$DOWNLOAD_TYPE" == "多線程" ]; then
        # aria2c command
        $DOWNLOAD_CMD "$FILENAME" "$URL"
    else
        # wget command
        $DOWNLOAD_CMD "$TARGET_FILE_PATH" "$URL"
    fi

    if [ $? -ne 0 ]; then
        echo "[!] 錯誤：無法下載 $FILENAME。請檢查網絡連接或 URL 是否正確。"
    else
        echo "[+] $FILENAME 下載完成！"
    fi
done

echo ""
echo "💡 字典設置完成。你現在可以使用它們了！例如用於 dirsearch:"
# Construct the dirsearch command with all downloaded wordlists
DIRSEARCH_WORDLISTS=""
for URL in "${WORDLIST_URLS[@]}"; do
    FILENAME=$(basename "$URL")
    if [ -f "$WORDLISTS_DIR/$FILENAME" ]; then
        if [ -z "$DIRSEARCH_WORDLISTS" ]; then
            DIRSEARCH_WORDLISTS="$WORDLISTS_DIR/$FILENAME"
        else
            DIRSEARCH_WORDLISTS="$DIRSEARCH_WORDLISTS,$WORDLISTS_DIR/$FILENAME"
        fi
    fi
done

echo "   python3 URL_FINDER/dirsearch/dirsearch.py -u http://planning.htb/ -e php,txt,html,zip --full-url -w $DIRSEARCH_WORDLISTS"
echo "   注意：dirsearch 的 -w 參數可以接受多個字典文件，用逗號分隔。"
echo "" 