#!/bin/bash

# 检查是否有.tar.gz文件
if ls *.tar.gz 1> /dev/null 2>&1; then
  # 循环遍历所有的.tar.gz文件
  for file in *.tar.gz; do
    # 提取文件名（不包含扩展名）
    filename=$(basename "$file" .tar.gz)
    
    # 创建目标目录（如果不存在）
    mkdir -p "$filename"
    
    # 解压文件到目标目录
    tar -zxvf "$file" -C "$filename"
    
    echo "已解压 $file 到 $filename 目录"
  done
else
  echo "没有找到任何.tar.gz文件"
fi

