import { useEffect, useRef, useCallback } from 'react';

type WsMessage = { type: string; [key: string]: any };

export function useWebSocket(auctionId: string | null, onMessage: (msg: WsMessage) => void) {

  const wsRef = useRef<WebSocket | null>(null);

  const onMsgRef = useRef(onMessage);

  onMsgRef.current = onMessage;


  useEffect(() => {

    if (!auctionId) return;

    const token = localStorage.getItem('token');

    if (!token) return;


    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';

    const host = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8000';

    const url = `${protocol}://${host}/ws/auctions/${auctionId}?token=${token}`;


    const ws = new WebSocket(url);

    wsRef.current = ws;


    ws.onmessage = (event) => {

      try { onMsgRef.current(JSON.parse(event.data)); } catch { /* ignore */ }

    };


    ws.onclose = () => { wsRef.current = null; };


    return () => { ws.close(); wsRef.current = null; };

  }, [auctionId]);


  const send = useCallback((msg: object) => {

    wsRef.current?.send(JSON.stringify(msg));

  }, []);


  return { send };

}
