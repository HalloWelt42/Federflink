/**
 * Wortweiser Diff fuer die Korrektur-Vorschau (gruen = hinzugefuegt,
 * rot durchgestrichen = entfernt, sonst unveraendert). LCS ueber Tokens
 * (Woerter und Zwischenraeume), ausreichend fuer kurze Texte.
 */

export type DiffTeil = { typ: 'gleich' | 'hinzu' | 'weg'; text: string }

function zerlege(s: string): string[] {
  return s.match(/\s+|\S+/g) ?? []
}

export function wortDiff(a: string, b: string): DiffTeil[] {
  const at = zerlege(a)
  const bt = zerlege(b)
  const n = at.length
  const m = bt.length

  // LCS-Laengentabelle
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array<number>(m + 1).fill(0))
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i][j] = at[i] === bt[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1])
    }
  }

  const teile: DiffTeil[] = []
  const schiebe = (typ: DiffTeil['typ'], text: string) => {
    const letzter = teile[teile.length - 1]
    if (letzter && letzter.typ === typ) letzter.text += text
    else teile.push({ typ, text })
  }

  let i = 0
  let j = 0
  while (i < n && j < m) {
    if (at[i] === bt[j]) {
      schiebe('gleich', at[i])
      i++
      j++
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      schiebe('weg', at[i])
      i++
    } else {
      schiebe('hinzu', bt[j])
      j++
    }
  }
  while (i < n) schiebe('weg', at[i++])
  while (j < m) schiebe('hinzu', bt[j++])
  return teile
}
