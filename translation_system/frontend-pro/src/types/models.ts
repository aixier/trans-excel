/**
 * 核心数据模型定义
 */

// ========== 用户与权限 ==========
export interface User {
  id: string
  username: string
  email: string
  avatar?: string
  role: UserRole
  permissions: Permission[]
  lastActiveAt: Date
  createdAt: Date
}

export enum UserRole {
  ADMIN = 'admin',
  TRANSLATOR = 'translator',
  REVIEWER = 'reviewer',
  VIEWER = 'viewer'
}

export interface Permission {
  resource: string
  action: string
}

// ========== 项目管理 ==========
export interface Project {
  id: string
  name: string
  description?: string
  status: ProjectStatus
  owner: User
  members: ProjectMember[]
  sourceLanguage: Language
  targetLanguages: Language[]
  gameBackground?: string
  regionCode?: RegionCode
  terminology?: Terminology[]
  createdAt: Date
  updatedAt: Date
}

export enum ProjectStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  ARCHIVED = 'archived'
}

export interface ProjectMember {
  user: User
  role: ProjectRole
  joinedAt: Date
}

export enum ProjectRole {
  OWNER = 'owner',
  MANAGER = 'manager',
  TRANSLATOR = 'translator',
  REVIEWER = 'reviewer',
  VIEWER = 'viewer'
}

// ========== 翻译数据 ==========
export interface TranslationTask {
  id: string
  projectId: string
  fileName: string
  fileSize: number
  status: TaskStatus
  progress: TranslationProgress
  config: TranslationConfig
  result?: TranslationResult
  error?: string
  createdBy: string
  createdAt: Date
  completedAt?: Date
}

export enum TaskStatus {
  PENDING = 'pending',
  UPLOADING = 'uploading',
  ANALYZING = 'analyzing',
  TRANSLATING = 'translating',
  REVIEWING = 'reviewing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export interface TranslationProgress {
  total: number
  completed: number
  failed: number
  skipped: number
  percentage: number
  estimatedTimeRemaining?: number
  currentSheet?: string
  currentRow?: number
}

export interface TranslationConfig {
  sourceLanguage?: Language
  targetLanguages: Language[]
  batchSize: number
  maxConcurrent: number
  regionCode?: RegionCode
  gameBackground?: string
  autoDetect: boolean
  preservePlaceholders: boolean
  useTerminology: boolean
  maxIterations: number
  qualityThreshold?: number
}

export interface TranslationResult {
  downloadUrl: string
  totalRows: number
  translatedRows: number
  failedRows: number
  statistics: TranslationStatistics
}

export interface TranslationStatistics {
  totalTokens: number
  totalCost: number
  averageQuality: number
  apiCalls: number
  duration: number
}

// ========== Excel/表格数据 ==========
export interface ExcelData {
  filename: string
  sheets: Sheet[]
  metadata: FileMetadata
}

export interface Sheet {
  name: string
  rows: Row[]
  columns: Column[]
  totalRows: number
  totalColumns: number
}

export interface Row {
  id: string
  index: number
  cells: Cell[]
}

export interface Column {
  id: string
  index: number
  name: string
  type: ColumnType
  language?: Language
  isTranslatable: boolean
}

export enum ColumnType {
  TEXT = 'text',
  NUMBER = 'number',
  DATE = 'date',
  FORMULA = 'formula'
}

export interface Cell {
  id: string
  rowId: string
  columnId: string
  value: string
  formattedValue?: string
  translation?: Translation
  metadata?: CellMetadata
}

export interface CellMetadata {
  format?: string
  style?: CellStyle
  comment?: string
  validation?: CellValidation
}

export interface CellStyle {
  backgroundColor?: string
  color?: string
  fontWeight?: string
  fontSize?: number
}

export interface CellValidation {
  type: 'list' | 'range' | 'regex'
  value: any
  errorMessage?: string
}

export interface FileMetadata {
  size: number
  mimeType: string
  lastModified: Date
  encoding?: string
}

// ========== 翻译核心 ==========
export interface Translation {
  id: string
  source: string
  target: string
  language: Language
  status: TranslationStatus
  quality?: QualityScore
  suggestions?: TranslationSuggestion[]
  metadata?: TranslationMetadata
  history?: TranslationHistory[]
}

export enum TranslationStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  REVIEWED = 'reviewed',
  APPROVED = 'approved',
  REJECTED = 'rejected'
}

export interface TranslationSuggestion {
  text: string
  confidence: number
  source: 'ai' | 'tm' | 'terminology'
}

export interface TranslationMetadata {
  translator: string
  reviewer?: string
  translatedAt: Date
  reviewedAt?: Date
  iterations: number
  apiProvider: string
  modelVersion: string
}

export interface TranslationHistory {
  version: number
  text: string
  changedBy: string
  changedAt: Date
  reason?: string
}

export interface QualityScore {
  overall: number
  accuracy: number
  fluency: number
  terminology: number
  formatting: number
  level: QualityLevel
  issues?: QualityIssue[]
}

export enum QualityLevel {
  EXCELLENT = 'excellent',
  GOOD = 'good',
  FAIR = 'fair',
  POOR = 'poor'
}

export interface QualityIssue {
  type: IssueType
  severity: IssueSeverity
  description: string
  position?: number
  suggestion?: string
}

export enum IssueType {
  INCONSISTENCY = 'inconsistency',
  PLACEHOLDER = 'placeholder',
  TERMINOLOGY = 'terminology',
  GRAMMAR = 'grammar',
  SPELLING = 'spelling'
}

export enum IssueSeverity {
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

// ========== 术语管理 ==========
export interface Terminology {
  id: string
  projectId?: string
  source: string
  translations: Map<Language, string>
  category?: string
  context?: string
  notes?: string
  isApproved: boolean
  createdBy: string
  createdAt: Date
}

// ========== 协作功能 ==========
export interface Comment {
  id: string
  cellId?: string
  rowId?: string
  content: string
  author: User
  mentions?: string[]
  resolved: boolean
  replies?: Comment[]
  createdAt: Date
  updatedAt?: Date
}

export interface Activity {
  id: string
  type: ActivityType
  actor: User
  target: ActivityTarget
  description: string
  metadata?: Record<string, any>
  timestamp: Date
}

export enum ActivityType {
  CELL_UPDATE = 'cell_update',
  COMMENT_ADD = 'comment_add',
  FILE_UPLOAD = 'file_upload',
  TASK_COMPLETE = 'task_complete',
  REVIEW_SUBMIT = 'review_submit'
}

export interface ActivityTarget {
  type: 'cell' | 'row' | 'sheet' | 'project' | 'task'
  id: string
  name?: string
}

export interface CursorPosition {
  userId: string
  cellId: string
  color: string
  timestamp: Date
}

// ========== 语言和地区 ==========
export interface Language {
  code: string
  name: string
  nativeName: string
  direction: 'ltr' | 'rtl'
}

export enum RegionCode {
  NA = 'na',  // North America
  SA = 'sa',  // South America
  EU = 'eu',  // Europe
  ME = 'me',  // Middle East
  AS = 'as'   // Asia
}

export interface RegionInfo {
  code: RegionCode
  name: string
  description: string
  culturalNotes?: string
  translationGuidelines?: string
}

// ========== 实时协作 ==========
export interface CollaborationState {
  onlineUsers: User[]
  activeEditors: Map<string, string> // cellId -> userId
  cursors: Map<string, CursorPosition>
  locks: Map<string, CellLock>
}

export interface CellLock {
  cellId: string
  userId: string
  lockedAt: Date
  expiresAt: Date
}

// ========== WebSocket消息 ==========
export interface WebSocketMessage {
  type: WSMessageType
  payload: any
  timestamp: Date
  sender?: string
}

export enum WSMessageType {
  // 连接管理
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  PING = 'ping',
  PONG = 'pong',

  // 用户状态
  USER_JOIN = 'user:join',
  USER_LEAVE = 'user:leave',
  USER_CURSOR = 'user:cursor',

  // 数据同步
  CELL_UPDATE = 'cell:update',
  CELL_LOCK = 'cell:lock',
  CELL_UNLOCK = 'cell:unlock',

  // 协作功能
  COMMENT_ADD = 'comment:add',
  COMMENT_UPDATE = 'comment:update',
  COMMENT_DELETE = 'comment:delete',

  // 翻译任务
  TRANSLATION_PROGRESS = 'translation:progress',
  TRANSLATION_COMPLETE = 'translation:complete'
}