export const formatSalaryAmount = (value: number | string): string =>
  String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
