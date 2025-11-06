export async function sendAnswers(answers) {
  try {
    // Updated to use the correct plan creation endpoint as specified in context
    const response = await fetch("http://127.0.0.1:8000/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(answers),
    });

    if (!response.ok) {
      console.error("Backend returned non-OK:", response.status, await response.text());
      throw new Error("Failed to create plan");
    }

    return await response.json();
  } catch (error) {
    console.error("Error calling backend:", error);
    throw error;
  }
}

export async function sendMagicLink(email) {
  try {
    const response = await fetch("http://127.0.0.1:8000/auth/magic-link", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      console.error("Backend returned non-OK:", response.status, await response.text());
      throw new Error("Magic link failed");
    }

    return await response.json();
  } catch (error) {
    console.error("Error calling backend:", error);
    throw error;
  }
}

export async function verifyToken(email, token) {
  try {
    const response = await fetch("http://127.0.0.1:8000/auth/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, token }),
    });

    if (!response.ok) {
      console.error("Backend returned non-OK:", response.status, await response.text());
      throw new Error("Token verification failed");
    }

    return await response.json();
  } catch (error) {
    console.error("Error calling backend:", error);
    throw error;
  }
}

export async function createCheckoutSession(planId, userId, sessionToken) {
  try {
    const response = await fetch("http://127.0.0.1:8000/checkout/session", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${sessionToken}`,
      },
      body: JSON.stringify({ plan_id: planId, user_id: userId }),
    });

    if (!response.ok) {
      console.error("Backend returned non-OK:", response.status, await response.text());
      throw new Error("Checkout failed");
    }

    return await response.json();
  } catch (error) {
    console.error("Error calling backend:", error);
    throw error;
  }
}