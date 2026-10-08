import { useEffect, useRef, useState } from 'react'

// Connects to the gateway's live feed and keeps the last `maxEvents` events
// in state. Reconnects automatically if the socket drops.
export function useLiveFeed(maxEvents = 30) {
  const [events, setEvents] = useState([])
  const [connected, setConnected] = useState(false)
  const socketRef = useRef(null)
  const retryRef = useRef(null)

  useEffect(() => {
    let cancelled = false

    function connect() {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const base = import.meta.env.VITE_WS_BASE || `${protocol}://${window.location.hostname}:8000`
      const socket = new WebSocket(`${base}/ws/live-feed`)
      socketRef.current = socket

      socket.onopen = () => !cancelled && setConnected(true)
      socket.onclose = () => {
        if (cancelled) return
        setConnected(false)
        retryRef.current = setTimeout(connect, 2500)
      }
      socket.onerror = () => socket.close()
      socket.onmessage = (msg) => {
        try {
          const payload = JSON.parse(msg.data)
          if (payload.type === 'new_analysis') {
            setEvents(prev => [{ id: payload.id, ...payload.data }, ...prev].slice(0, maxEvents))
          }
        } catch {
          // ignore malformed frames
        }
      }
    }

    connect()
    return () => {
      cancelled = true
      clearTimeout(retryRef.current)
      socketRef.current?.close()
    }
  }, [maxEvents])

  return { events, connected }
}
