/**
 * 全部女声音色（kokoro）：练习页与设置页共用这份名单。
 * value 会原样传给后端 /api/audio 与 /api/sentences/generate。
 */
export const VOICE_OPTIONS = [
  { value: 'af_heart', label: 'Heart · af_heart（美·最自然）' },
  { value: 'af_bella', label: 'Bella · af_bella（美·活泼）' },
  { value: 'af_nicole', label: 'Nicole（美·轻柔）' },
  { value: 'af_sarah', label: 'Sarah · af_sarah（美）' },
  { value: 'af_kore', label: 'Kore · af_kore（美）' },
  { value: 'af_nova', label: 'Nova · af_nova（美）' },
  { value: 'af_sky', label: 'Sky · af_sky（美）' },
  { value: 'af_aoede', label: 'Aoede · af_aoede（美）' },
  { value: 'af_alloy', label: 'Alloy · af_alloy（美）' },
  { value: 'af_jessica', label: 'Jessica · af_jessica（美）' },
  { value: 'af_river', label: 'River · af_river（美）' },
  { value: 'bf_emma', label: 'Emma · bf_emma（英）' },
  { value: 'bf_isabella', label: 'Isabella · bf_isabella（英）' },
  { value: 'bf_alice', label: 'Alice · bf_alice（英）' },
  { value: 'bf_lily', label: 'Lily · bf_lily（英）' },
]

/** 兼容旧值：aria/guy/完整声音名 -> 现在的女声 key */
export function normalizeVoice(v) {
  const known = VOICE_OPTIONS.map(o => o.value)
  if (known.includes(v)) return v
  return 'af_heart'
}
