/**
 * 全部女声音色（kokoro）：练习页与设置页共用这份名单。
 * value 会原样传给后端 /api/audio 与 /api/sentences/generate。
 */
export const VOICE_OPTIONS = [
  { value: 'af_heart', label: 'Heart（美·最自然）' },
  { value: 'af_bella', label: 'Bella（美·活泼）' },
  { value: 'af_nicole', label: 'Nicole（美·轻柔）' },
  { value: 'af_sarah', label: 'Sarah（美）' },
  { value: 'af_kore', label: 'Kore（美）' },
  { value: 'af_nova', label: 'Nova（美）' },
  { value: 'af_sky', label: 'Sky（美）' },
  { value: 'af_aoede', label: 'Aoede（美）' },
  { value: 'af_alloy', label: 'Alloy（美）' },
  { value: 'af_jessica', label: 'Jessica（美）' },
  { value: 'af_river', label: 'River（美）' },
  { value: 'bf_emma', label: 'Emma（英）' },
  { value: 'bf_isabella', label: 'Isabella（英）' },
  { value: 'bf_alice', label: 'Alice（英）' },
  { value: 'bf_lily', label: 'Lily（英）' },
]

/** 兼容旧值：aria/guy/完整声音名 -> 现在的女声 key */
export function normalizeVoice(v) {
  const known = VOICE_OPTIONS.map(o => o.value)
  if (known.includes(v)) return v
  return 'af_heart'
}
