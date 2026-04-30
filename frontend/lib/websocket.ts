/**
 * websocket.ts
 * Creates a WebSocket that routes:
 *   - JSON { type:"status", data:{...} }  → onStatus callback
 *   - JSON { type:"ping" }                → ignored
 *   - Any other text                      → onMessage callback
 */
export function createLogSocket(
  url: string,
  onMessage: (line: string) => void,
  onStatus:  (data: object) => void,
): WebSocket {
  const ws = new WebSocket(url)

  ws.onmessage = (e: MessageEvent) => {
    const raw = e.data as string
    // Try to parse as JSON first
    try {
      const d = JSON.parse(raw)
      if (!d || typeof d !== 'object') throw new Error('not object')
      if (d.type === 'ping') return
      if (d.type === 'status' && d.data) {
        onStatus(d.data)
        return
      }
      // JSON but not a known type — pass as log line
      onMessage(raw)
    } catch {
      // Plain text log line
      if (raw.trim()) onMessage(raw)
    }
  }

  return ws
}
