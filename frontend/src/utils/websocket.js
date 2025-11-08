/**
 * WebSocket Client Utility
 * Manages WebSocket connections to the backend
 * Uses environment variables to construct the correct WebSocket URL
 */

import { API_CONFIG } from "../constants";

/**
 * Get WebSocket URL from API base URL
 * Converts http://127.0.0.1:8000 to ws://127.0.0.1:8000/ws
 * Supports both localhost and network IPs
 * 
 * @returns {string} WebSocket URL
 */
export function getWebSocketUrl() {
  // Get API base URL from constants (which uses environment variables)
  const apiUrl = API_CONFIG.BASE_URL || "http://127.0.0.1:8000";
  
  // Convert http/https to ws/wss
  let wsUrl = apiUrl.replace(/^http/, "ws");
  
  // Ensure it ends with /ws
  if (!wsUrl.endsWith("/ws")) {
    // Remove trailing slash if present, then add /ws
    wsUrl = wsUrl.replace(/\/$/, "") + "/ws";
  }
  
  console.log(`[WebSocket] Connecting to: ${wsUrl}`);
  return wsUrl;
}

/**
 * Create a WebSocket connection
 * Automatically uses the correct backend URL
 * 
 * @param {string} path - Optional path to append (default: "/ws")
 * @param {Object} options - WebSocket options
 * @returns {WebSocket} WebSocket instance
 */
export function createWebSocketConnection(path = "/ws", options = {}) {
  const apiUrl = API_CONFIG.BASE_URL || "http://127.0.0.1:8000";
  
  // Convert http/https to ws/wss
  let wsUrl = apiUrl.replace(/^http/, "ws");
  
  // Remove trailing slash if present
  wsUrl = wsUrl.replace(/\/$/, "");
  
  // Append path (ensure it starts with /)
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  wsUrl = wsUrl + normalizedPath;
  
  console.log(`[WebSocket] Creating connection to: ${wsUrl}`);
  
  try {
    const ws = new WebSocket(wsUrl);
    return ws;
  } catch (error) {
    console.error(`[WebSocket] Failed to create connection:`, error);
    throw error;
  }
}

/**
 * WebSocket Client Class
 * Manages WebSocket connection with automatic reconnection and error handling
 */
export class WebSocketClient {
  constructor(url, options = {}) {
    this.url = url || getWebSocketUrl();
    this.options = {
      reconnectInterval: options.reconnectInterval || 3000,
      maxReconnectAttempts: options.maxReconnectAttempts || 10,
      ...options
    };
    
    this.ws = null;
    this.reconnectAttempts = 0;
    this.shouldReconnect = true;
    this.listeners = new Map();
    this.isConnecting = false;
  }

  /**
   * Connect to WebSocket server
   */
  connect() {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      console.log("[WebSocket] Already connected or connecting");
      return;
    }

    this.isConnecting = true;
    console.log(`[WebSocket] Connecting to: ${this.url}`);

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = (event) => {
        console.log("[WebSocket] Connected successfully");
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.emit("open", event);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit("message", data);
        } catch (error) {
          // If not JSON, emit raw message
          this.emit("message", event.data);
        }
      };

      this.ws.onerror = (error) => {
        // Don't log as error - WebSocket is optional and failures are non-critical
        console.warn("[WebSocket] Connection error (non-critical):", error);
        this.isConnecting = false;
        this.emit("error", error);
      };

      this.ws.onclose = (event) => {
        // Don't log as error - WebSocket is optional
        // Only log non-normal closures
        if (event.code !== 1000 && event.code !== 1001) { // 1000 = normal closure, 1001 = going away
          // Only log first few connection failures to avoid console spam
          if (this.reconnectAttempts < 2) {
            console.warn(`[WebSocket] Connection closed (code: ${event.code}) - WebSocket is optional, content will still load`);
          }
        }
        this.isConnecting = false;
        this.emit("close", event);

        // Attempt to reconnect if not intentionally closed
        // But limit retries and reduce logging to avoid spam
        if (this.shouldReconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
          this.reconnectAttempts++;
          // Only log first attempt to reduce console noise
          if (this.reconnectAttempts === 1) {
            console.log(`[WebSocket] Attempting to reconnect... (WebSocket is optional)`);
          }
          setTimeout(() => {
            if (this.shouldReconnect && !this.isConnecting) {
              this.connect();
            }
          }, this.options.reconnectInterval);
        } else if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
          // Silent failure - WebSocket is optional and non-critical
          // Don't log as error since it's expected if backend WebSocket isn't available
          this.emit("maxReconnectAttemptsReached");
        }
      };
    } catch (error) {
      console.error("[WebSocket] Failed to create connection:", error);
      this.isConnecting = false;
      this.emit("error", error);
    }
  }

  /**
   * Send message through WebSocket
   */
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = typeof data === "string" ? data : JSON.stringify(data);
      this.ws.send(message);
    } else {
      console.warn("[WebSocket] Cannot send message - connection not open");
    }
  }

  /**
   * Close WebSocket connection
   */
  close() {
    this.shouldReconnect = false;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Add event listener
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  /**
   * Remove event listener
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * Emit event to listeners
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }

  /**
   * Get connection state
   */
  getReadyState() {
    if (!this.ws) return WebSocket.CONNECTING;
    return this.ws.readyState;
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

