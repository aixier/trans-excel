import { UploadPanel } from '@modules/upload'

const UploadPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">上传Excel文件</h1>
        <UploadPanel />
      </div>
    </div>
  )
}

export default UploadPage