export const getDashboardErrorMessage = (error: unknown): string => {
  if (typeof error !== 'object' || error === null) {
    return 'Проверьте соединение и попробуйте ещё раз.'
  }

  if ('data' in error && typeof error.data === 'object' && error.data !== null) {
    const data = error.data as Record<string, unknown>
    if (typeof data.detail === 'string') {
      return data.detail
    }
  }

  if ('error' in error && typeof error.error === 'string') {
    return error.error
  }

  return 'Проверьте соединение и попробуйте ещё раз.'
}
