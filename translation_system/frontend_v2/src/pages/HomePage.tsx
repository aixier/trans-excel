import { Button, Card, Typography, Space } from 'antd'
import { useNavigate } from 'react-router-dom'
import { UploadOutlined, FileTextOutlined, TranslationOutlined, BarChartOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

const HomePage = () => {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <Title level={1} className="text-center mb-4">
          Translation System V2
        </Title>
        <Paragraph className="text-center text-gray-600 mb-12">
          高效、智能的Excel文件翻译系统
        </Paragraph>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card
            hoverable
            onClick={() => navigate('/upload')}
            className="text-center"
          >
            <Space direction="vertical" size="large">
              <UploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              <Title level={4}>上传文件</Title>
              <Paragraph className="text-gray-600">
                上传Excel文件开始翻译
              </Paragraph>
            </Space>
          </Card>

          <Card
            hoverable
            className="text-center"
          >
            <Space direction="vertical" size="large">
              <FileTextOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              <Title level={4}>文件分析</Title>
              <Paragraph className="text-gray-600">
                分析文件内容和结构
              </Paragraph>
            </Space>
          </Card>

          <Card
            hoverable
            className="text-center"
          >
            <Space direction="vertical" size="large">
              <TranslationOutlined style={{ fontSize: 48, color: '#722ed1' }} />
              <Title level={4}>执行翻译</Title>
              <Paragraph className="text-gray-600">
                使用AI进行智能翻译
              </Paragraph>
            </Space>
          </Card>

          <Card
            hoverable
            className="text-center"
          >
            <Space direction="vertical" size="large">
              <BarChartOutlined style={{ fontSize: 48, color: '#fa541c' }} />
              <Title level={4}>进度监控</Title>
              <Paragraph className="text-gray-600">
                实时监控翻译进度
              </Paragraph>
            </Space>
          </Card>
        </div>

        <div className="text-center mt-12">
          <Button
            type="primary"
            size="large"
            icon={<UploadOutlined />}
            onClick={() => navigate('/upload')}
          >
            开始使用
          </Button>
        </div>
      </div>
    </div>
  )
}

export default HomePage