export interface ResumeImportProps {
  onFileSelected?: (file: File) => void
  onResumeAnalyze?: (file: File) => void
  isResumeLoading?: boolean
  analysisError?: string | null
}
