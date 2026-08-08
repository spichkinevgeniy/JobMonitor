export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class TelegramAuthorizationError extends Error {
  constructor() {
    super('Откройте Mini App внутри Telegram.')
    this.name = 'TelegramAuthorizationError'
  }
}
