#!/bin/bash

echo "Testing API connectivity to Aliyun Dashscope..."
echo "================================"

# 测试DNS解析
echo -e "\n1. Testing DNS resolution:"
nslookup dashscope.aliyuncs.com

# 测试基本连接
echo -e "\n2. Testing HTTPS connectivity:"
curl -I --connect-timeout 10 https://dashscope.aliyuncs.com 2>&1 | head -20

# 测试API endpoint
echo -e "\n3. Testing API endpoint with timeout settings:"
curl -X GET \
  --connect-timeout 10 \
  --max-time 30 \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  https://dashscope.aliyuncs.com/compatible-mode/v1/models 2>&1 | head -50

echo -e "\n4. Testing SSL certificate:"
echo | openssl s_client -connect dashscope.aliyuncs.com:443 -servername dashscope.aliyuncs.com 2>/dev/null | openssl x509 -noout -dates

echo -e "\nConnectivity test completed."
