from scapy.all import rdpcap
import os

def find_ftp_passwords(pcap_file):
    # 讀取 .pcap 檔案
    try:
        packets = rdpcap(pcap_file)
    except FileNotFoundError:
        print(f"找不到檔案: {pcap_file}")
        return
    except Exception as e:
        print(f"讀取檔案失敗: {e}")
        return

    username = None
    password = None

    # 遍歷封包
    for packet in packets:
        if packet.haslayer("TCP") and packet["TCP"].dport == 21:  # FTP 端口 21
            if packet.haslayer("Raw"):  # 有原始數據
                raw_data = packet["Raw"].load.decode("utf-8", errors="ignore")
                if "USER" in raw_data:
                    username = raw_data.split("USER")[1].strip()
                    print(f"找到使用者名稱: {username}")
                if "PASS" in raw_data:
                    password = raw_data.split("PASS")[1].strip()
                    print(f"找到密碼: {password}")

    # 輸出結果
    if username and password:
        print(f"\nFTP 憑證: {username}:{password}")
    else:
        print("沒找到完整的 FTP 憑證")

if __name__ == "__main__":
    # 設定 .pcap 路徑
    pcap_path = os.path.join(os.path.dirname(__file__), "..", "..", "pacp")
    pcap_name = input("請輸入 .pcap 檔案名稱（例如 capture.pcap）：")
    pcap_file = os.path.join(pcap_path, pcap_name)
    find_ftp_passwords(pcap_file)