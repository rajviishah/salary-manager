export function lookupOptions(values: string[] | undefined) {
  return (values ?? []).map((value) => ({ label: value, value }))
}

export function lookupOptionsWithCurrent(
  values: string[] | undefined,
  current?: string | null,
) {
  const list = [...(values ?? [])]
  if (current && !list.includes(current)) list.unshift(current)
  return lookupOptions(list)
}

export function autoCompleteOptions(values: string[] | undefined) {
  return (values ?? []).map((value) => ({ value }))
}
