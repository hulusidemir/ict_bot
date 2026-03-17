import { useEffect, useRef, useState, useCallback } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = window.location.origin;

export default function useSocket() {
  const [connected, setConnected] = useState(false);
  const [signals, setSignals] = useState([]);
  const [trades, setTrades] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    const socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
    });
    socketRef.current = socket;

    socket.on('connect', () => setConnected(true));
    socket.on('disconnect', () => setConnected(false));

    socket.on('new_signal', (data) => {
      setSignals((prev) => [data, ...prev].slice(0, 200));
    });

    socket.on('trade_opened', (data) => {
      setTrades((prev) => [data, ...prev].slice(0, 200));
    });

    socket.on('trade_closed', (data) => {
      setTrades((prev) =>
        prev.map((t) => (t.id === data.id ? { ...t, ...data } : t))
      );
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return { connected, signals, trades, setSignals, setTrades };
}
