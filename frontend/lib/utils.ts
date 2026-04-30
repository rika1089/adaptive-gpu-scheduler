import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function fmt(n: number, decimals = 1): string {
  return n.toFixed(decimals)
}

export function fmtMs(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.round(ms)}ms`
}

export function fmtPct(n: number, decimals = 1): string {
  return `${(n * 100).toFixed(decimals)}%`
}
