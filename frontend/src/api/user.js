// src/api/user.js
import { apiRequest } from "./client";

export async function getUser() {
  return apiRequest("/user", "GET");
}

export async function updateUserProfile(profileData) {
  return apiRequest("/user", "PATCH", profileData);
}
