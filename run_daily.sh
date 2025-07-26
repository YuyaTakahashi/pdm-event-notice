#!/bin/bash

# 日次実行用スクリプト
# 実行ログを記録し、エラーハンドリングも含む

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# ログファイルの設定
LOG_DIR="./logs"
LOG_FILE="$LOG_DIR/daily_run_$(date +%Y%m%d).log"

# ログディレクトリを作成
mkdir -p "$LOG_DIR"

# 実行開始時刻を記録
echo "=== 日次実行開始: $(date) ===" >> "$LOG_FILE"

# Pythonスクリプトを実行
python3 main.py >> "$LOG_FILE" 2>&1

# 実行結果を記録
if [ $? -eq 0 ]; then
    echo "=== 実行成功: $(date) ===" >> "$LOG_FILE"
else
    echo "=== 実行失敗: $(date) ===" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE" 