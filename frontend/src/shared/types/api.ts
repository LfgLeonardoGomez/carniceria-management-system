export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  detail: string
  statusCode: number
}
