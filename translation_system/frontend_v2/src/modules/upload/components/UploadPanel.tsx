import React from 'react'
import { Upload, Button, Progress, message, Card } from 'antd'
import { UploadOutlined, FileExcelOutlined } from '@ant-design/icons'
import { useUploadStore } from '../store'
import { useNavigate } from 'react-router-dom'
import type { UploadProps } from 'antd'

export const UploadPanel: React.FC = () => {
  const { upload, uploading, progress, error, file } = useUploadStore()
  const navigate = useNavigate()

  const handleBeforeUpload: UploadProps['beforeUpload'] = (file) => {
    // Validate file type
    const isExcel =
      file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      file.type === 'application/vnd.ms-excel' ||
      file.name.endsWith('.xlsx') ||
      file.name.endsWith('.xls')

    if (!isExcel) {
      message.error('只能上传Excel文件（.xlsx 或 .xls）!')
      return false
    }

    // Validate file size (10MB limit)
    const isLt10M = file.size / 1024 / 1024 < 10
    if (!isLt10M) {
      message.error('文件大小不能超过10MB!')
      return false
    }

    // Start upload with navigate function
    upload(file, navigate)
    return false // Prevent default upload behavior
  }

  return (
    <Card className="shadow-lg">
      <div className="p-8">
        <Upload.Dragger
          beforeUpload={handleBeforeUpload}
          showUploadList={false}
          disabled={uploading}
          accept=".xlsx,.xls"
        >
          <p className="ant-upload-drag-icon">
            <FileExcelOutlined style={{ fontSize: 64, color: '#52c41a' }} />
          </p>
          <p className="ant-upload-text text-xl font-semibold">
            点击或拖拽文件到这里上传
          </p>
          <p className="ant-upload-hint">
            支持 .xlsx 和 .xls 格式，最大 10MB
          </p>
        </Upload.Dragger>

        {file && !uploading && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center">
              <FileExcelOutlined className="text-2xl text-blue-500 mr-3" />
              <div>
                <p className="font-semibold">{file.name}</p>
                <p className="text-sm text-gray-600">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
          </div>
        )}

        {uploading && (
          <div className="mt-6">
            <Progress
              percent={progress}
              status="active"
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
            <p className="text-center mt-2 text-gray-600">
              正在上传中，请稍候...
            </p>
          </div>
        )}

        {error && (
          <div className="mt-6 p-4 bg-red-50 rounded-lg border border-red-200">
            <p className="text-red-600">
              <strong>错误:</strong> {error}
            </p>
          </div>
        )}

        {progress === 100 && !uploading && (
          <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
            <p className="text-green-600">
              <strong>成功!</strong> 文件已上传，正在跳转到分析页面...
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}