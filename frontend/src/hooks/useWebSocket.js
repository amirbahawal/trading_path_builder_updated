/**
 * React Hook for WebSocket Connections
 * Manages WebSocket connection lifecycle in React components
 * Automatically uses the correct backend URL from environment variables
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { WebSocketClient, getWebSocketUrl } from "../utils/websocket";

/**
 * Custom hook for WebSocket connections
 * 
 * @param {string} path - WebSocket path (default: "/ws")
 * @param {Object} options - WebSocket options (reconnectInterval, maxReconnectAttempts, etc.)
 * @param {boolean} autoConnect - Whether to auto-connect on mount (default: true)
 * @returns {Object} WebSocket state and methods
 */
export function useWebSocket(path = "/ws", options = {}, autoConnect = true) {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [lastMessage, setLastMessage] = useState(null);
  const wsClientRef = useRef(null);

  // Get WebSocket URL
  const wsUrl = useRef(getWebSocketUrl()).current;

  // Initialize WebSocket client
  useEffect(() => {
    if (!wsClientRef.current) {
      wsClientRef.current = new WebSocketClient(wsUrl, options);
      
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

    // Auto-connect if enabled
    if (autoConnect && !isConnected && !isConnecting) {
      setIsConnecting(true);
      wsClientRef.current.connect();
    }

    // Cleanup on unmount
    return () => {
      if (wsClientRef.current) {
        wsClientRef.current.close();
        wsClientRef.current = null;
      }
    };
  }, [autoConnect, wsUrl, options]);

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
        if (data.type === messageType || data.event === messageType) {
          callback(data);
        }
      };
      wsClientRef.current.on("message", messageHandler);
      return () => wsClientRef.current.off("message", messageHandler);
    }
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

  useEffect(() => {
    if (!planId || !isConnected) return;

    // Subscribe to plan unlock updates
    const unsubscribe = subscribe("plan_unlocked", (data) => {
      if (data.plan_id === planId) {
        onUnlockUpdate?.(data);
      }
    });

    // Subscribe to plan update events
    const unsubscribeUpdate = subscribe("plan_updated", (data) => {
      if (data.plan_id === planId) {
        onUnlockUpdate?.(data);
      }
    });

    // Request current plan status
    sendMessage({
      type: "subscribe",
      plan_id: planId
    });

    return () => {
      unsubscribe?.();
      unsubscribeUpdate?.();
    };
  }, [planId, isConnected, subscribe, sendMessage, onUnlockUpdate]);

  return {
    isConnected,
    error
  };
}

export default useWebSocket;

