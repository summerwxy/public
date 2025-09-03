#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 方便自己修改D2r物品名稱的腳本

import json
from pathlib import Path
import shutil
import csv
import requests
import os
import sys
import hashlib
import re


__version__ = '0.0.2'

URL_SCRIPT = "https://raw.githubusercontent.com/summerwxy/public/refs/heads/main/d2r_my_name.py"

def get_remote_version_and_code():
  """下載遠端腳本，取出版本號和完整內容"""
  resp = requests.get(URL_SCRIPT, timeout=5)
  resp.raise_for_status()
  code = resp.text

  # 用正則找 __version__ 定義
  match = re.search(r'__version__\s*=\s*["\'](.+?)["\']', code)
  remote_version = match.group(1) if match else None
  return remote_version, code

def check_update():
  """檢查更新並自動覆蓋"""
  try:
    remote_version, remote_code = get_remote_version_and_code()
    if not remote_version:
      print("⚠️ 無法取得遠端版本號，略過更新檢查。")
      return

    if remote_version != __version__:
      print(f"🔔 發現新版本 {remote_version} (目前 {__version__})")
      choice = input("要更新嗎？(y/n): ").strip().lower()
      if choice == "y":
        script_path = os.path.abspath(sys.argv[0])
        with open(script_path, "w", encoding="utf-8") as f:
          f.write(remote_code)
        print("✅ 更新完成，請重新執行本程式。")
        sys.exit(0)
    else:
      print(f"目前已是最新版本 {__version__}。")
  except Exception as e:
    print("⚠️ 檢查更新失敗：", e)

def main():
  print("")
  print("== 檔案名稱裡面有包含 wxy 就是找 小幃電腦的安裝路徑==")
  print("== 檔案名稱裡面有包含 ssd 就是找 黑狗電腦的安裝路徑==")
  print("== 檔案名稱裡面有包含 va 就是找 口水電腦的安裝路徑==")
  print("")

  # 原始檔路徑
  py_file = os.path.basename(__file__)
  wxy_path = r"D:\Program Files\Diablo II Resurrected\Mods\Wxy\Wxy.mpq"
  ssd_path = r"D:\Diablo II Resurrected\Mods\ssd\ssd.mpq"
  va_path = r"C:\Program Files (x86)\Diablo II Resurrected\Mods\va\va.mpq"
  the_path = ''

  if 'wxy' in py_file:
    the_path = wxy_path
  elif 'ssd' in py_file:
    the_path = ssd_path
  elif 'va' in py_file:
    the_path = va_path
  else:
    print("蛤? 改一下檔案名稱才知道誰在執行的")
    sys.exit()


  json_path = Path(the_path + r"\Data\Local\Lng\Strings\item-names.json")
  bak_path = json_path.with_suffix(json_path.suffix + ".bak")  # item-names.json.bak

  # CSV 公開連結
  csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRG-SzLZG61Xz9QsisKAD7gV1AdKLnGe2zQlTHdNrB8Fn4QATrXpLzB-ciXaQ5DH1-vt2XCTFa_g3Bv/pub?gid=1362474824&single=true&output=csv"


  # 1. 如果沒有備份檔，就先建立
  if not bak_path.exists():
      shutil.copy2(json_path, bak_path)
      print(f"已建立備份檔：{bak_path}")

  # 2. 讀取備份檔（用 utf-8-sig 去除 BOM）
  with open(bak_path, "r", encoding="utf-8-sig") as f:
      data = json.load(f)

  # 3. 建立 id → obj 映射
  key_map = {obj["Key"]: obj for obj in data if "id" in obj}

  # 4. 下載 CSV
  response = requests.get(csv_url)
  response.encoding = 'utf-8'  # 確保中文正常
  lines = response.text.splitlines()
  reader = csv.DictReader(lines)  # CSV 有標題列

  no_show_mdk = False
  while True:
      answer = input("是否使用 MDK mod 的篩選?\n    no: 正常顯示\n    yes: 根據 MDK mod 不顯示沒用處的裝備\n\n請輸入:").strip().lower()
      if answer == "yes":
          no_show_mdk = True
          break
      elif answer == "no":
          break
      else:
          print("看不懂你的輸入，請輸入 yes 或 no。")

  print('\n')

  # 5. 遍歷 CSV 更新對應物件
  for row in reader:
      obj_key = row["Key"].strip()  # CSV A欄是 id
      if obj_key in key_map:
          obj = key_map[obj_key]
          new_text = obj.get("zhTW", "")

          # 如果 D 欄有值 → 完全替代
          if row["new_text"].strip():
              new_text = row["new_text"].strip()
          
          if row['append_text_mdk'].strip():
              new_text += row['append_text_mdk'].strip()

          # 如果 E 欄有值 → 附加
          if row["append_text"].strip():
              new_text += row["append_text"].strip()

          if row['no_show'].strip() == 'y':
              new_text = ''

          if row['no_show_mdk'].strip() == 'y':
              new_text = ''
          
          # 更新 zhTW_bak
          obj["zhTW"] = new_text

  # 6. 覆蓋原始檔案（寫回 UTF-8 with BOM）
  with open(json_path, "w", encoding="utf-8-sig") as f:
      json.dump(data, f, ensure_ascii=False, indent=2)

  print(f"已完成修改，並覆蓋：{json_path}")
  input("按 Enter 鍵結束...")


if __name__ == "__main__":
  print("檢查版本...")
  check_update()
  print("程式繼續執行...")
  main()
