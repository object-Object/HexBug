import { use } from "react";

import { discordSDKPromise } from "./useDiscordSDK";

export function useDiscordAuth() {
  return use(authPromise);
}

const authPromise = authenticate();

// Keep in sync with bot/src/HexBug/cogs/api.py
interface TokenRequest {
  code: string;
}

// Keep in sync with bot/src/HexBug/cogs/api.py
interface TokenResponse {
  access_token: string;
}

async function authenticate() {
  const discordSDK = await discordSDKPromise;

  const authOutput = await discordSDK.commands.authorize({
    client_id: import.meta.env.VITE_CLIENT_ID,
    response_type: "code",
    prompt: "none",
    scope: ["identify"],
  });

  const tokenResponse = await fetch("/api/activity/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(authOutput satisfies TokenRequest),
  });
  const { access_token } = (await tokenResponse.json()) as TokenResponse;

  return await discordSDK.commands.authenticate({ access_token });
}
