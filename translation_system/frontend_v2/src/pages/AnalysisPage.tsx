import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Button, Spin, Alert, Table, Tag, Row, Col, Statistic, Space, Progress, Descriptions, Tabs } from 'antd'
import { FileExcelOutlined, TranslationOutlined, ReloadOutlined, CheckCircleOutlined, ClockCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { apiClient } from '@core/api/client'
import type { TabsProps } from 'antd'

interface AnalysisData {
  session_id: string
  file_name: string
  file_size: number
  upload_time: string
  sheet_count: number
  sheets: SheetInfo[]
  task_summary: TaskSummary
  total_cells: number
  translation_needed: number
  estimated_tokens: number
  estimated_cost: number
}

interface SheetInfo {
  index: number
  name: string
  row_count: number
  column_count: number
  cell_count: number
  translation_tasks: number
  color_cells: {
    yellow: number
    blue: number
    other: number
  }
}

interface TaskSummary {
  total: number
  yellow_cells: number
  blue_cells: number
  sheets_affected: number
  estimated_time_minutes: number
}

const AnalysisPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    if (!sessionId) {
      setError('会话ID不存在')
      setLoading(false)
      return
    }
    fetchAnalysisData()
  }, [sessionId])

  const fetchAnalysisData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get(`/analyze/status/${sessionId}`)

      // Transform backend response to match our interface
      const analysisInfo = response.analysis || {}
      const statistics = analysisInfo.statistics || {}
      const fileInfo = analysisInfo.file_info || {}

      // Extract colored cells count (yellow + blue) from statistics
      const coloredCells = statistics.sheets?.[0]?.colored_cells || 0

      // Transform sheets data from statistics
      const sheets = statistics.sheets?.map((sheet: any, index: number) => ({
        index,
        name: sheet.name,
        row_count: sheet.rows,
        column_count: sheet.cols,
        cell_count: sheet.cells,
        translation_tasks: sheet.colored_cells || 0,
        color_cells: {
          yellow: sheet.colored_cells || 0,  // For now, assume all colored are yellow
          blue: 0,
          other: 0
        }
      })) || []

      const transformedData: AnalysisData = {
        session_id: response.session_id || sessionId,
        file_name: fileInfo.filename || 'unknown.xlsx',
        file_size: statistics.file_size || 1024000,  // Default 1MB if not provided
        upload_time: new Date().toISOString(),
        sheet_count: fileInfo.sheet_count || 0,
        sheets: sheets,
        task_summary: {
          total: coloredCells,
          yellow_cells: coloredCells,  // Assume all colored cells are yellow for now
          blue_cells: 0,
          sheets_affected: sheets.filter((s: any) => s.translation_tasks > 0).length,
          estimated_time_minutes: Math.ceil(coloredCells * 0.5)
        },
        total_cells: statistics.total_cells || 0,
        translation_needed: coloredCells,
        estimated_tokens: coloredCells * 100,
        estimated_cost: coloredCells * 0.05
      }

      setAnalysisData(transformedData)
    } catch (err: any) {
      setError(err.message || '获取分析数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleStartTranslation = () => {
    navigate(`/translation/${sessionId}`)
  }

  const handleReanalyze = () => {
    fetchAnalysisData()
  }

  const handleBackToUpload = () => {
    navigate('/upload')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Spin size="large" tip="正在加载分析数据..." />
      </div>
    )
  }

  if (error || !analysisData) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <Alert
            message="加载失败"
            description={error || '无法获取分析数据'}
            type="error"
            showIcon
            action={
              <Space>
                <Button size="small" onClick={handleReanalyze}>
                  重试
                </Button>
                <Button size="small" type="primary" onClick={handleBackToUpload}>
                  返回上传
                </Button>
              </Space>
            }
          />
        </div>
      </div>
    )
  }

  const sheetColumns = [
    {
      title: '序号',
      dataIndex: 'index',
      key: 'index',
      width: 80,
      render: (index: number) => index + 1
    },
    {
      title: 'Sheet名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <span className="font-medium">{name}</span>
      )
    },
    {
      title: '行×列',
      key: 'dimensions',
      render: (sheet: SheetInfo) => (
        <span>{sheet.row_count} × {sheet.column_count}</span>
      )
    },
    {
      title: '黄色单元格',
      key: 'yellow',
      render: (sheet: SheetInfo) => (
        <Tag color="gold">{sheet.color_cells.yellow}</Tag>
      )
    },
    {
      title: '蓝色单元格',
      key: 'blue',
      render: (sheet: SheetInfo) => (
        <Tag color="blue">{sheet.color_cells.blue}</Tag>
      )
    },
    {
      title: '翻译任务数',
      dataIndex: 'translation_tasks',
      key: 'translation_tasks',
      render: (tasks: number) => (
        <Tag color={tasks > 0 ? 'green' : 'default'}>{tasks}</Tag>
      )
    }
  ]

  const tabItems: TabsProps['items'] = [
    {
      key: 'overview',
      label: '概览',
      children: (
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card className="h-full">
              <Statistic
                title="总翻译任务"
                value={analysisData.task_summary.total}
                prefix={<TranslationOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card className="h-full">
              <Statistic
                title="黄色单元格"
                value={analysisData.task_summary.yellow_cells}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card className="h-full">
              <Statistic
                title="蓝色单元格"
                value={analysisData.task_summary.blue_cells}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card className="h-full">
              <Statistic
                title="预估时间"
                value={analysisData.task_summary.estimated_time_minutes}
                suffix="分钟"
                prefix={<ClockCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )
    },
    {
      key: 'sheets',
      label: 'Sheet详情',
      children: (
        <Table
          dataSource={analysisData.sheets}
          columns={sheetColumns}
          rowKey="index"
          pagination={false}
          size="middle"
        />
      )
    },
    {
      key: 'cost',
      label: '成本预估',
      children: (
        <Card>
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Statistic
                title="预估Token数"
                value={analysisData.estimated_tokens}
                suffix="tokens"
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="预估成本"
                value={analysisData.estimated_cost}
                prefix="¥"
                precision={2}
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
          </Row>
          <div className="mt-6">
            <Progress
              percent={Math.min((analysisData.translation_needed / analysisData.total_cells) * 100, 100)}
              status="active"
              format={(percent) => `${analysisData.translation_needed} / ${analysisData.total_cells} 单元格`}
            />
          </div>
        </Card>
      )
    }
  ]

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <Card className="mb-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <FileExcelOutlined className="text-4xl text-green-600" />
              <div>
                <h1 className="text-2xl font-bold mb-1">文件分析结果</h1>
                <p className="text-gray-600">{analysisData.file_name}</p>
              </div>
            </div>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={handleReanalyze}>
                重新分析
              </Button>
              <Button
                type="primary"
                size="large"
                icon={<TranslationOutlined />}
                onClick={handleStartTranslation}
                disabled={analysisData.task_summary.total === 0}
              >
                开始翻译
              </Button>
            </Space>
          </div>
        </Card>

        {/* File Info */}
        <Card className="mb-6">
          <Descriptions title="文件信息" bordered column={{ xxl: 4, xl: 3, lg: 3, md: 2, sm: 1, xs: 1 }}>
            <Descriptions.Item label="会话ID">{analysisData.session_id}</Descriptions.Item>
            <Descriptions.Item label="文件大小">{(analysisData.file_size / 1024 / 1024).toFixed(2)} MB</Descriptions.Item>
            <Descriptions.Item label="Sheet数量">{analysisData.sheet_count}</Descriptions.Item>
            <Descriptions.Item label="上传时间">{new Date(analysisData.upload_time).toLocaleString()}</Descriptions.Item>
          </Descriptions>
        </Card>

        {/* Analysis Results Tabs */}
        <Card>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
          />
        </Card>

        {/* Summary Alert */}
        {analysisData.task_summary.total > 0 ? (
          <Alert
            className="mt-6"
            message="分析完成"
            description={`发现 ${analysisData.task_summary.total} 个需要翻译的单元格，分布在 ${analysisData.task_summary.sheets_affected} 个Sheet中。预计需要 ${analysisData.task_summary.estimated_time_minutes} 分钟完成。`}
            type="success"
            showIcon
            icon={<CheckCircleOutlined />}
            action={
              <Button
                type="primary"
                onClick={handleStartTranslation}
              >
                立即开始翻译
              </Button>
            }
          />
        ) : (
          <Alert
            className="mt-6"
            message="无需翻译"
            description="未发现需要翻译的单元格。请检查Excel文件中是否有黄色或蓝色标记的单元格。"
            type="warning"
            showIcon
            icon={<ExclamationCircleOutlined />}
            action={
              <Button onClick={handleBackToUpload}>
                重新上传
              </Button>
            }
          />
        )}
      </div>
    </div>
  )
}

export default AnalysisPage