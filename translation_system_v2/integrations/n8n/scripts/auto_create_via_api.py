#!/usr/bin/env python3
"""
自动通过 n8n REST API 创建和激活翻译工作流
解决方案：使用官方 n8n API 实现完全自动化的工作流创建

重要说明：
- n8n API Key 必须通过 UI 生成，环境变量中的 N8N_API_KEY 无法用于 API 认证
- 请先访问 http://localhost:5678 → Settings → n8n API → Create API Key
- 然后通过以下方式之一提供 API Key：
  1. 环境变量: export N8N_REAL_API_KEY="your_key"
  2. 命令行参数: --api-key "your_key"
  3. 交互式输入: --interactive
"""

import requests
import json
import time
import sys
import os
import argparse
import getpass

# n8n API 配置
N8N_HOST = os.getenv('N8N_HOST', 'localhost')
N8N_PORT = os.getenv('N8N_PORT', '5678')
N8N_BASE_URL = f"http://{N8N_HOST}:{N8N_PORT}/api/v1"

# 默认尝试从多个环境变量读取 API Key
N8N_API_KEY = (
    os.getenv('N8N_REAL_API_KEY') or  # 优先使用实际的 API Key
    os.getenv('N8N_API_KEY') or       # 兼容旧配置
    None
)

def get_api_headers(api_key):
    """生成 API 请求头"""
    return {
        'X-N8N-API-KEY': api_key,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

# 工作流定义（完整的Form Trigger工作流）
WORKFLOW_DEFINITION = {
    "name": "Excel翻译表单_自动创建",
    # 注意：创建时不能设置 active 字段，需要创建后再激活
    "nodes": [
        {
            "parameters": {
                "path": "trans",
                "formTitle": "📄 Excel翻译服务",
                "formDescription": "上传Excel文件进行AI翻译",
                "formFields": {
                    "values": [
                        {
                            "fieldLabel": "Excel文件",
                            "fieldType": "file",
                            "requiredField": True
                        },
                        {
                            "fieldLabel": "目标语言",
                            "fieldType": "dropdown",
                            "fieldOptions": {
                                "values": [
                                    {"option": "英文", "value": "EN"},
                                    {"option": "泰文", "value": "TH"},
                                    {"option": "日文", "value": "JP"},
                                    {"option": "韩文", "value": "KR"}
                                ]
                            },
                            "requiredField": True
                        },
                        {
                            "fieldLabel": "术语库（可选）",
                            "fieldType": "text",
                            "requiredField": False,
                            "placeholder": "输入术语库名称，留空使用默认"
                        }
                    ]
                },
                "responseMode": "onReceived",
                "formSubmittedText": "翻译任务已提交！请保存返回的会话ID以便查询进度。"
            },
            "id": "form_trigger_node",
            "name": "翻译表单",
            "type": "n8n-nodes-base.formTrigger",
            "typeVersion": 2,
            "position": [240, 300],
            "webhookId": ""  # n8n会自动生成
        },
        {
            "parameters": {
                "method": "POST",
                "url": "http://backend:8013/api/tasks/split",
                "sendBody": True,
                "contentType": "multipart-form-data",
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "file",
                            "value": "={{ $binary.data }}"
                        },
                        {
                            "name": "source_lang",
                            "value": "CH"
                        },
                        {
                            "name": "target_langs",
                            "value": "={{ $json['目标语言'] }}"
                        },
                        {
                            "name": "glossary_name",
                            "value": "={{ $json['术语库（可选）'] || 'default' }}"
                        }
                    ]
                },
                "options": {
                    "timeout": 300000  # 5分钟超时
                }
            },
            "id": "http_request_node",
            "name": "提交翻译任务",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.1,
            "position": [460, 300]
        },
        {
            "parameters": {
                "respondWith": "json",
                "responseBody": "={{ { \"success\": true, \"session_id\": $json.session_id, \"message\": \"任务已创建\", \"status_url\": \"http://localhost:8013/api/tasks/split/status/\" + $json.session_id, \"download_url\": \"http://localhost:8013/api/download/\" + $json.session_id, \"tips\": \"请保存session_id，完成后访问download_url下载结果\" } }}"
            },
            "id": "respond_node",
            "name": "返回结果",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1,
            "position": [680, 300]
        }
    ],
    "connections": {
        "翻译表单": {
            "main": [
                [
                    {
                        "node": "提交翻译任务",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        },
        "提交翻译任务": {
            "main": [
                [
                    {
                        "node": "返回结果",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        }
    },
    "settings": {
        "executionOrder": "v1"
    }
    # 注意：staticData 和 tags 是只读字段，创建时不能包含
}


def check_n8n_health():
    """检查 n8n 服务健康状态"""
    try:
        response = requests.get(f"http://{N8N_HOST}:{N8N_PORT}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ n8n 服务运行正常")
            return True
        else:
            print(f"❌ n8n 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到 n8n: {e}")
        return False


def check_backend_health():
    """检查后端服务健康状态"""
    try:
        response = requests.get("http://localhost:8013/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
            return True
        else:
            print(f"❌ 后端健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到后端: {e}")
        return False


def delete_existing_workflows(headers):
    """删除已存在的同名工作流"""
    try:
        # 获取所有工作流
        response = requests.get(f"{N8N_BASE_URL}/workflows", headers=headers, timeout=10)

        if response.status_code == 200:
            workflows = response.json().get('data', [])
            deleted_count = 0

            for workflow in workflows:
                if '翻译' in workflow.get('name', '') or 'trans' in workflow.get('name', '').lower():
                    workflow_id = workflow.get('id')
                    print(f"🗑️  删除已存在的工作流: {workflow.get('name')} (ID: {workflow_id})")

                    delete_response = requests.delete(
                        f"{N8N_BASE_URL}/workflows/{workflow_id}",
                        headers=headers,
                        timeout=10
                    )

                    if delete_response.status_code in [200, 204]:
                        deleted_count += 1
                        print(f"   ✅ 已删除")
                    else:
                        print(f"   ⚠️  删除失败: {delete_response.status_code}")

            if deleted_count > 0:
                print(f"✅ 已删除 {deleted_count} 个旧工作流")
                time.sleep(2)  # 等待删除完成
            else:
                print("ℹ️  没有需要删除的旧工作流")
            return True
        else:
            print(f"⚠️  无法获取工作流列表: {response.status_code}")
            return False

    except Exception as e:
        print(f"⚠️  删除旧工作流时出错: {e}")
        return False


def create_workflow(headers):
    """通过 API 创建工作流"""
    try:
        print("\n📝 正在创建工作流...")

        response = requests.post(
            f"{N8N_BASE_URL}/workflows",
            headers=headers,
            json=WORKFLOW_DEFINITION,
            timeout=30
        )

        if response.status_code in [200, 201]:
            workflow = response.json().get('data', response.json())
            workflow_id = workflow.get('id')
            print(f"✅ 工作流创建成功！")
            print(f"   工作流ID: {workflow_id}")
            print(f"   工作流名称: {workflow.get('name')}")
            return workflow_id
        else:
            print(f"❌ 创建工作流失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 创建工作流时出错: {e}")
        return None


def activate_workflow(workflow_id, headers):
    """激活工作流"""
    try:
        print(f"\n🚀 正在激活工作流 {workflow_id}...")

        # 先获取完整工作流
        get_response = requests.get(
            f"{N8N_BASE_URL}/workflows/{workflow_id}",
            headers=headers,
            timeout=10
        )

        if get_response.status_code != 200:
            print(f"❌ 无法获取工作流: {get_response.status_code}")
            return False

        workflow_data = get_response.json().get('data', get_response.json())

        # 修改 active 状态
        workflow_data['active'] = True

        # 使用 PUT 方法更新整个工作流
        response = requests.put(
            f"{N8N_BASE_URL}/workflows/{workflow_id}",
            headers=headers,
            json=workflow_data,
            timeout=30
        )

        if response.status_code == 200:
            workflow = response.json().get('data', response.json())
            is_active = workflow.get('active', False)

            if is_active:
                print(f"✅ 工作流已激活！")
                return True
            else:
                print(f"⚠️  工作流激活状态异常: {is_active}")
                return False
        else:
            print(f"❌ 激活工作流失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 激活工作流时出错: {e}")
        return False


def get_workflow_info(workflow_id, headers):
    """获取工作流详细信息"""
    try:
        response = requests.get(
            f"{N8N_BASE_URL}/workflows/{workflow_id}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get('data', response.json())
        else:
            print(f"⚠️  无法获取工作流信息: {response.status_code}")
            return None

    except Exception as e:
        print(f"⚠️  获取工作流信息时出错: {e}")
        return None


def extract_form_url(workflow_info):
    """从工作流信息中提取表单URL"""
    try:
        # 查找Form Trigger节点
        nodes = workflow_info.get('nodes', [])
        for node in nodes:
            if node.get('type') == 'n8n-nodes-base.formTrigger':
                webhook_id = node.get('webhookId', '')
                path = node.get('parameters', {}).get('path', 'trans')

                if webhook_id:
                    form_url = f"http://{N8N_HOST}:{N8N_PORT}/form/{webhook_id}"
                    return form_url

        return None
    except Exception as e:
        print(f"⚠️  提取表单URL时出错: {e}")
        return None


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='n8n 工作流自动创建脚本',
        epilog='示例: python3 auto_create_via_api.py --api-key "n8n_api_xxxxx"'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='n8n API Key（从 UI 生成）'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='交互式输入 API Key'
    )
    parser.add_argument(
        '--skip-backend-check',
        action='store_true',
        help='跳过后端健康检查'
    )
    return parser.parse_args()


def get_api_key_interactive():
    """交互式获取 API Key"""
    print("\n" + "=" * 60)
    print("📝 API Key 获取指南")
    print("=" * 60)
    print("\n如果你还没有 API Key，请按照以下步骤生成：\n")
    print("1. 打开浏览器访问: http://localhost:5678")
    print("2. 登录后点击右上角头像 → Settings")
    print("3. 找到 'n8n API' 或 'API Keys' 选项")
    print("4. 点击 'Create API Key' 按钮")
    print("5. 复制生成的 key（只显示一次！）")
    print("\n" + "=" * 60)

    api_key = getpass.getpass("\n请粘贴你的 API Key（输入不可见）: ").strip()

    if not api_key:
        print("\n❌ API Key 不能为空")
        return None

    if not api_key.startswith('n8n_api_'):
        print(f"\n⚠️  警告: API Key 格式可能不正确")
        print(f"   通常应该以 'n8n_api_' 开头")
        confirm = input("是否继续？(y/N): ").strip().lower()
        if confirm != 'y':
            return None

    return api_key


def main():
    """主函数"""
    print("=" * 60)
    print("🤖 n8n 工作流自动创建脚本")
    print("   通过 REST API 实现完全自动化")
    print("=" * 60)

    # 解析命令行参数
    args = parse_arguments()

    # 获取 API Key（优先级：命令行参数 > 交互式输入 > 环境变量）
    api_key = None

    if args.api_key:
        api_key = args.api_key
        print("\n✅ 使用命令行提供的 API Key")
    elif args.interactive:
        api_key = get_api_key_interactive()
        if not api_key:
            sys.exit(1)
    elif N8N_API_KEY:
        api_key = N8N_API_KEY
        print(f"\n✅ 使用环境变量中的 API Key")
    else:
        print("\n❌ 错误: 未提供 API Key")
        print("\n请使用以下方式之一提供 API Key：")
        print("  1. 环境变量: export N8N_REAL_API_KEY='your_key'")
        print("  2. 命令行参数: --api-key 'your_key'")
        print("  3. 交互式输入: --interactive")
        print("\n💡 如何生成 API Key? 查看文档: N8N_API_KEY_SETUP.md")
        sys.exit(1)

    # 生成请求头
    headers = get_api_headers(api_key)

    # 步骤1: 健康检查
    print("\n[步骤1] 健康检查...")
    if not check_n8n_health():
        print("\n❌ n8n 服务未运行，请先启动服务")
        print("   运行命令: cd docker && docker-compose up -d")
        sys.exit(1)

    if not args.skip_backend_check and not check_backend_health():
        print("\n⚠️  后端服务未运行，工作流将无法正常工作")
        print("   建议启动后端服务: cd ../../../backend_v2 && python3 main.py")

    # 步骤2: 删除旧工作流
    print("\n[步骤2] 清理旧工作流...")
    delete_existing_workflows(headers)

    # 步骤3: 创建新工作流
    print("\n[步骤3] 创建新工作流...")
    workflow_id = create_workflow(headers)

    if not workflow_id:
        print("\n❌ 工作流创建失败")
        print("\n常见原因：")
        print("  1. API Key 无效或过期")
        print("  2. n8n 版本不支持 API Key 认证")
        print("  3. 权限不足")
        print("\n💡 解决方案：")
        print("  - 重新生成 API Key: http://localhost:5678 → Settings → n8n API")
        print("  - 检查 n8n 日志: docker logs translation_n8n")
        sys.exit(1)

    # 步骤4: 激活工作流
    print("\n[步骤4] 激活工作流...")
    time.sleep(2)  # 等待工作流完全创建

    if not activate_workflow(workflow_id, headers):
        print("\n❌ 工作流激活失败")
        sys.exit(1)

    # 步骤5: 获取工作流信息和表单URL
    print("\n[步骤5] 获取表单访问地址...")
    time.sleep(2)  # 等待webhook注册

    workflow_info = get_workflow_info(workflow_id, headers)
    if workflow_info:
        form_url = extract_form_url(workflow_info)

        print("\n" + "=" * 60)
        print("🎉 工作流创建成功！")
        print("=" * 60)
        print(f"工作流ID: {workflow_id}")
        print(f"工作流名称: {workflow_info.get('name')}")
        print(f"激活状态: {'✅ 已激活' if workflow_info.get('active') else '❌ 未激活'}")

        if form_url:
            print(f"\n📋 表单访问地址:")
            print(f"   {form_url}")
            print(f"\n💡 使用方法:")
            print(f"   1. 在浏览器访问上述URL")
            print(f"   2. 上传Excel文件")
            print(f"   3. 选择目标语言")
            print(f"   4. 提交后保存返回的session_id")
            print(f"   5. 使用session_id查询状态和下载结果")
        else:
            print(f"\n⚠️  无法获取表单URL，请手动在 n8n UI 中查看")
            print(f"   访问: http://{N8N_HOST}:{N8N_PORT}")

        print("\n" + "=" * 60)
    else:
        print("\n⚠️  无法获取工作流详细信息")

    print("\n✅ 自动化创建完成！")


if __name__ == "__main__":
    main()
