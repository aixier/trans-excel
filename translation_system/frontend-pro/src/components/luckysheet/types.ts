/**
 * Luckysheet 类型定义
 */

export interface LuckysheetConfig {
  container: string
  title?: string
  lang?: 'zh' | 'en' | 'es'
  data?: SheetData[]
  allowEdit?: boolean
  showtoolbar?: boolean
  showinfobar?: boolean
  showsheetbar?: boolean
  showstatisticBar?: boolean
  sheetFormulaBar?: boolean
  enableAddRow?: boolean
  enableAddCol?: boolean
  userInfo?: string
  devicePixelRatio?: number
  hook?: LuckysheetHooks
  [key: string]: any
}

export interface SheetData {
  name: string
  color?: string
  index: number
  status: number
  order: number
  hide?: number
  row?: number
  column?: number
  celldata?: CellData[]
  config?: SheetConfig
  scrollLeft?: number
  scrollTop?: number
  luckysheet_select_save?: any[]
  luckysheet_conditionformat_save?: any[]
  calcChain?: any[]
  isPivotTable?: boolean
  pivotTable?: any
  filter_select?: any
  filter?: any
  luckysheet_alternateformat_save?: any[]
  dataVerification?: any
  hyperlink?: any
  images?: any
}

export interface CellData {
  r: number  // 行号
  c: number  // 列号
  v?: CellValue | string | number
}

export interface CellValue {
  v?: string | number  // 原始值
  m?: string           // 显示值
  ct?: CellType        // 单元格类型
  bg?: string          // 背景色
  fc?: string          // 字体颜色
  ff?: string          // 字体
  fs?: number          // 字体大小
  it?: 0 | 1           // 斜体
  bl?: 0 | 1           // 粗体
  tb?: 0 | 1 | 2       // 文本换行 0截断 1溢出 2换行
  vt?: 0 | 1 | 2       // 垂直对齐 0中间 1上 2下
  ht?: 0 | 1 | 2       // 水平对齐 0居中 1左 2右
  mc?: MergeCell       // 合并单元格
  f?: string           // 公式
}

export interface CellType {
  fa: string  // 格式定义
  t: 's' | 'n' | 'b' | 'd'  // 类型：字符串、数字、布尔、日期
}

export interface MergeCell {
  r: number  // 合并起始行
  c: number  // 合并起始列
  rs: number // 合并行数
  cs: number // 合并列数
}

export interface SheetConfig {
  merge?: Record<string, MergeCell>
  rowlen?: Record<string, number>
  columnlen?: Record<string, number>
  rowhidden?: Record<string, number>
  colhidden?: Record<string, number>
  borderInfo?: any[]
}

export interface LuckysheetHooks {
  cellEditBefore?: (range: any) => boolean | void
  cellEditAfter?: (oldValue: any, newValue: any, isRefresh: boolean) => void
  cellUpdated?: (r: number, c: number, oldValue: any, newValue: any, isRefresh: boolean) => void
  cellRenderBefore?: (cell: any, position: any, sheet: any, ctx: any) => any
  cellRenderAfter?: (cell: any, position: any, sheet: any, ctx: any) => void
  cellAllRenderBefore?: (data: any[], sheet: any, ctx: any) => any[]
  rangeSelect?: (range: any) => void
  rangeMoveBefore?: (range: any) => boolean | void
  rangeMoveAfter?: (oldRange: any, newRange: any) => void
  rangeEditBefore?: (range: any) => boolean | void
  rangeEditAfter?: (range: any, data: any) => void
  rangeCopyBefore?: (range: any) => boolean | void
  rangePasteBefore?: (range: any) => boolean | void
  rangePasteAfter?: (range: any, data: any) => void
  rangeCutBefore?: (range: any) => boolean | void
  rangeDeleteBefore?: (range: any) => boolean | void
  rangeClearBefore?: (range: any) => boolean | void
  sheetCreateBefore?: (sheet: any) => boolean | void
  sheetCreateAfter?: (sheet: any) => void
  sheetMoveBefore?: (index1: number, index2: number) => boolean | void
  sheetMoveAfter?: (index1: number, index2: number, sheet: any) => void
  sheetDeleteBefore?: (sheet: any) => boolean | void
  sheetDeleteAfter?: (sheet: any) => void
  sheetEditNameBefore?: (oldName: string, newName: string) => boolean | void
  sheetEditNameAfter?: (oldName: string, newName: string) => void
  sheetEditColorBefore?: (sheet: any, color: string) => boolean | void
  sheetEditColorAfter?: (sheet: any, color: string) => void
  sheetZoomBefore?: (zoom: number) => boolean | void
  sheetZoomAfter?: (zoom: number) => void
  sheetActivateBefore?: (index: number, sheet: any) => boolean | void
  sheetActivateAfter?: (index: number, sheet: any) => void
  workbookCreateBefore?: (options: any) => any
  workbookCreateAfter?: (options: any) => void
  workbookDestroyBefore?: () => boolean | void
  workbookDestroyAfter?: () => void
  updated?: (operate: any) => void
  imageInsertBefore?: (url: string) => boolean | void
  imageInsertAfter?: (url: string, image: any) => void
  imageDeleteBefore?: (image: any) => boolean | void
  imageDeleteAfter?: (image: any) => void
  commentInsertBefore?: (cell: any) => boolean | void
  commentInsertAfter?: (cell: any, comment: any) => void
  commentDeleteBefore?: (cell: any, comment: any) => boolean | void
  commentDeleteAfter?: (cell: any, comment: any) => void
  commentUpdateBefore?: (cell: any, oldComment: any, newComment: any) => boolean | void
  commentUpdateAfter?: (cell: any, comment: any) => void
  rowInsertBefore?: (row: number, count: number, direction: 'top' | 'bottom') => boolean | void
  rowInsertAfter?: (row: number, count: number, direction: 'top' | 'bottom', sheet: any) => void
  rowDeleteBefore?: (row: number[], count: number) => boolean | void
  rowDeleteAfter?: (row: number[], count: number, sheet: any) => void
  columnInsertBefore?: (column: number, count: number, direction: 'left' | 'right') => boolean | void
  columnInsertAfter?: (column: number, count: number, direction: 'left' | 'right', sheet: any) => void
  columnDeleteBefore?: (column: number[], count: number) => boolean | void
  columnDeleteAfter?: (column: number[], count: number, sheet: any) => void
}

// Luckysheet全局对象
declare global {
  interface Window {
    luckysheet: {
      create: (config: LuckysheetConfig) => void
      getAllSheets: () => SheetData[]
      getCurrentSheet: () => SheetData
      getCellValue: (r: number, c: number, sheet?: number) => CellValue | null
      setCellValue: (r: number, c: number, value: any, sheet?: number) => void
      setCellFormat: (r: number, c: number, attr: string, value: any, sheet?: number) => void
      getRange: () => any[]
      getRangeValue: (range?: any) => any[][]
      setRangeValue: (data: any[][], range?: any) => void
      refresh: () => void
      destroy: () => void
      loadData: (data: SheetData[]) => void
      exportExcel: (options?: { filename?: string; sheetName?: string }) => void
      getCellPosition: (r: number, c: number) => { top: number; left: number }
      setRangeShow: (range: any) => void
      [key: string]: any
    }
    luckyExcel: {
      transformExcelToLucky: (file: File | Blob) => Promise<SheetData[]>
      transformLuckyToExcel: (data: SheetData[], name: string) => void
    }
  }
}

export {}