export type CategoryAccent = {
  background: string
  border: string
  foreground: string
  glow: string
}

const fallbackAccent: CategoryAccent = {
  background: 'rgba(148, 163, 184, 0.14)',
  border: 'rgba(148, 163, 184, 0.48)',
  foreground: '#cbd5e1',
  glow: 'rgba(148, 163, 184, 0.16)',
}

const accents: Record<string, CategoryAccent> = {
  teknoloji: {
    background: 'rgba(139, 92, 246, 0.18)',
    border: 'rgba(167, 139, 250, 0.58)',
    foreground: '#ddd6fe',
    glow: 'rgba(139, 92, 246, 0.2)',
  },
  muzik: {
    background: 'rgba(236, 72, 153, 0.17)',
    border: 'rgba(244, 114, 182, 0.58)',
    foreground: '#fbcfe8',
    glow: 'rgba(236, 72, 153, 0.19)',
  },
  spor: {
    background: 'rgba(16, 185, 129, 0.16)',
    border: 'rgba(52, 211, 153, 0.56)',
    foreground: '#a7f3d0',
    glow: 'rgba(16, 185, 129, 0.18)',
  },
  egitim: {
    background: 'rgba(245, 158, 11, 0.16)',
    border: 'rgba(251, 191, 36, 0.58)',
    foreground: '#fde68a',
    glow: 'rgba(245, 158, 11, 0.18)',
  },
  sanat: {
    background: 'rgba(249, 115, 22, 0.16)',
    border: 'rgba(251, 146, 60, 0.58)',
    foreground: '#fed7aa',
    glow: 'rgba(249, 115, 22, 0.18)',
  },
  'is-dunyasi': {
    background: 'rgba(14, 165, 233, 0.16)',
    border: 'rgba(56, 189, 248, 0.58)',
    foreground: '#bae6fd',
    glow: 'rgba(14, 165, 233, 0.18)',
  },
}

export function getCategoryAccent(slug: string): CategoryAccent {
  return accents[slug] ?? fallbackAccent
}
