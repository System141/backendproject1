import { useEffect, useRef, useCallback, useState } from 'react';

type WsMessage = { type: string; [key: string]: any };

export function useWebSocket(auctionId: string | null, onMessage: (msg: WsMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const onMsgRef = useRef(onMessage);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  const retryCountRef = useRef(0);

  onMsgRef.current = onMessage;

  const connect = useCallback(() => {
    if (!auctionId) return;

    const token = localStorage.getItem('token');
    if (!token) return;

    setStatus('connecting');
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8000';
    const url = `${protocol}://${host}/ws/auctions/${auctionId}?token=${token}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('connected');
      retryCountRef.current = 0;
    };

    ws.onmessage = (event) => {
      try { onMsgRef.current(JSON.parse(event.data)); } catch { /* ignore */ }
    };

    ws.onclose = () => {
      wsRef.current = null;
      setStatus('disconnected');

      // Auto-reconnect with exponential backoff (max 30s)
      if (retryCountRef.current < 10) {
        const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 30000);
        retryCountRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(() => connect(), delay);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [auctionId]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      retryCountRef.current = 0;
      setStatus('disconnected');
    };
  }, [connect]);

  const send = useCallback((msg: object) => {
    wsRef.current?.send(JSON.stringify(msg));
  }, []);

  return { send, status };
}