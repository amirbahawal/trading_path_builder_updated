/**
 * React Hook for WebSocket Connections
 * Manages WebSocket connection lifecycle in React components
 * Automatically uses the correct backend URL from environment variables
 */

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { WebSocketClient, getWebSocketUrl } from "../utils/websocket";

/**
 * Custom hook for WebSocket connections
 * 
 * @param {string} _path - WebSocket path (deprecated, kept for compatibility, unused)
 * @param {Object} options - WebSocket options (reconnectInterval, maxReconnectAttempts, etc.)
 * @param {boolean} autoConnect - Whether to auto-connect on mount (default: true)
 * @returns {Object} WebSocket state and methods
 */
export function useWebSocket(_path = "/ws", options = {}, autoConnect = true) {
  // Note: path parameter is kept for API compatibility but WebSocket URL
  // is automatically derived from API_CONFIG.BASE_URL
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [lastMessage, setLastMessage] = useState(null);
  const wsClientRef = useRef(null);
  const optionsRef = useRef(options);
  const autoConnectRef = useRef(autoConnect);

  // Update refs when props change
  useEffect(() => {
    optionsRef.current = options;
    autoConnectRef.current = autoConnect;
  }, [options, autoConnect]);

  // Get WebSocket URL (memoized to prevent recreation)
  const wsUrl = useMemo(() => getWebSocketUrl(), []);

  // Initialize WebSocket client (only once on mount)
  useEffect(() => {
    if (!wsClientRef.current) {
      wsClientRef.current = new WebSocketClient(wsUrl, optionsRef.current);
      
      // Set up event listeners
      wsClientRef.current.on("open", () => {
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
      });

      wsClientRef.current.on("close", () => {
        setIsConnected(false);
        setIsConnecting(false);
      });

      wsClientRef.current.on("error", (err) => {
        setError(err);
        setIsConnecting(false);
      });

      wsClientRef.current.on("message", (data) => {
        setLastMessage(data);
      });
    }

    // Cleanup on unmount
    return () => {
      if (wsClientRef.current) {
        wsClientRef.current.close();
        wsClientRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  // Auto-connect effect (separate from initialization)
  useEffect(() => {
    if (autoConnectRef.current && wsClientRef.current && !isConnected && !isConnecting) {
      setIsConnecting(true);
      wsClientRef.current.connect();
    }
  }, [isConnected, isConnecting]);

  // Send message function
  const sendMessage = useCallback((data) => {
    if (wsClientRef.current && wsClientRef.current.isConnected()) {
      wsClientRef.current.send(data);
    } else {
      console.warn("[useWebSocket] Cannot send message - not connected");
      setError(new Error("WebSocket is not connected"));
    }
  }, []);

  // Connect function
  const connect = useCallback(() => {
    if (wsClientRef.current && !isConnected && !isConnecting) {
      setIsConnecting(true);
      wsClientRef.current.connect();
    }
  }, [isConnected, isConnecting]);

  // Disconnect function
  const disconnect = useCallback(() => {
    if (wsClientRef.current) {
      wsClientRef.current.close();
      setIsConnected(false);
      setIsConnecting(false);
    }
  }, []);

  // Subscribe to specific message types
  const subscribe = useCallback((messageType, callback) => {
    if (wsClientRef.current) {
      const messageHandler = (data) => {
        if (data && (data.type === messageType || data.event === messageType)) {
          callback(data);
        }
      };
      wsClientRef.current.on("message", messageHandler);
      return () => {
        if (wsClientRef.current) {
          wsClientRef.current.off("message", messageHandler);
        }
      };
    }
    // Return no-op cleanup function if client doesn't exist
    return () => {};
  }, []);

  return {
    isConnected,
    isConnecting,
    error,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    subscribe
  };
}

/**
 * Hook for plan unlock WebSocket updates
 * Listens for unlock status updates from the backend
 * 
 * @param {string} planId - Plan ID to listen for updates
 * @param {Function} onUnlockUpdate - Callback when unlock status updates
 * @returns {Object} WebSocket state
 */
export function usePlanUnlockWebSocket(planId, onUnlockUpdate) {
  const { isConnected, error, subscribe, sendMessage } = useWebSocket("/ws", {}, !!planId);
  const onUnlockUpdateRef = useRef(onUnlockUpdate);

  // Update callback ref when it changes
  useEffect(() => {
    onUnlockUpdateRef.current = onUnlockUpdate;
  }, [onUnlockUpdate]);

  useEffect(() => {
    if (!planId || !isConnected) return;

    // Subscribe to plan unlock updates
    const unsubscribe = subscribe("plan_unlocked", (data) => {
      if (data && data.plan_id === planId) {
        onUnlockUpdateRef.current?.(data);
      }
    });

    // Subscribe to plan update events
    const unsubscribeUpdate = subscribe("plan_updated", (data) => {
      if (data && data.plan_id === planId) {
        onUnlockUpdateRef.current?.(data);
      }
    });

    // Request current plan status
    try {
      sendMessage({
        type: "subscribe",
        plan_id: planId
      });
    } catch (err) {
      console.warn("[usePlanUnlockWebSocket] Failed to send subscription message:", err);
    }

    return () => {
      if (unsubscribe) unsubscribe();
      if (unsubscribeUpdate) unsubscribeUpdate();
    };
  }, [planId, isConnected, subscribe, sendMessage]);

  return {
    isConnected,
    error
  };
}

export default useWebSocket;

